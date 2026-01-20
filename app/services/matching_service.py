# app/services/matching_service.py
import numpy as np
import pickle
from sqlalchemy import cast, or_
from sqlalchemy.dialects.postgresql import JSONB

from app.models.job import Job
from app.models.user import User
from app.models.application import CV_File
from app.services.ai_engine.gemini_client import GeminiClient  # Cần để lấy embedding query mới


class JobMatcher:
    def __init__(self):
        self.ai_client = GeminiClient()

    def _normalize_skills(self, skills_input):
        if not skills_input:
            return set()
        if isinstance(skills_input, str):
            return set(s.strip().lower() for s in skills_input.split(','))
        if isinstance(skills_input, list):
            return set(s.strip().lower() for s in skills_input)
        return set()

    def _cosine_similarity(self, vec_a, vec_b):
        """Tính Cosine Similarity giữa 2 vector numpy"""
        if vec_a is None or vec_b is None:
            return 0.0

        # Chuyển đổi list về numpy array nếu cần
        a = np.array(vec_a)
        b = np.array(vec_b)

        if a.shape != b.shape:
            return 0.0

        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def get_user_profile_vector(self, user):
        """
        Lấy Vector đại diện cho User.
        Ưu tiên: Vector của CV chính > Vector sinh từ Bio
        """
        # 1. Thử lấy từ CV chính
        main_cv = CV_File.query.filter_by(user_id=user.id, is_main=True).first()
        if main_cv and main_cv.vector_embedding:
            # vector_embedding trong DB là PickleType -> Tự decode thành list/array
            return main_cv.vector_embedding

        # 2. Nếu không có CV, sinh vector nóng từ Bio (Tốn API AI)
        if user.bio:
            return self.ai_client.get_embedding(user.bio)

        return None

    def find_top_matches(self, user_id: int, limit=5, user_query_text=None):
        """
        Hàm Matching thông minh (Hybrid): Keyword + Vector Semantic
        """
        user = User.query.get(user_id)
        if not user:
            return []

        # --- GIAI ĐOẠN 1: PRE-FILTERING (LỌC THÔ BẰNG SQL) ---
        # Chỉ lấy những job có kỹ năng trùng hoặc đang Active để giảm tải tính toán
        user_skills = self._normalize_skills(user.bio)  # Hoặc lấy từ CV như code cũ

        # Nếu có user_query_text (người dùng chat cụ thể), ta ưu tiên tìm theo context đó
        if user_query_text:
            query_vector = self.ai_client.get_embedding(user_query_text)
        else:
            query_vector = self.get_user_profile_vector(user)

        # Lấy candidates (Ứng viên jobs tiềm năng)
        # Tối ưu: Nếu không có skill, lấy top 50 job mới nhất
        if not user_skills:
            candidates = Job.query.filter_by(is_active=True).order_by(Job.created_at.desc()).limit(50).all()
        else:
            # Dùng toán tử JSONB ?| như đã tối ưu trước đó
            user_skills_list = list(user_skills)
            candidates = Job.query.filter(
                Job.is_active == True,
                cast(Job.skills_required, JSONB).op('?|')(user_skills_list)
            ).limit(50).all()

        scored_jobs = []

        # --- GIAI ĐOẠN 2: SCORING (CHẤM ĐIỂM CHI TIẾT) ---
        for job in candidates:
            # 1. Điểm Keyword (Hard Skill Match) - Trọng số 40%
            job_skills = self._normalize_skills(job.skills_required)
            matched = user_skills.intersection(job_skills)
            missing = job_skills.difference(user_skills)

            if len(job_skills) > 0:
                keyword_score = (len(matched) / len(job_skills)) * 100
            else:
                keyword_score = 0

            # 2. Điểm Semantic (Vector Match) - Trọng số 60%
            # Logic: Nếu user đang chat tìm việc cụ thể, so sánh với query.
            # Nếu không, so sánh với CV/Bio của user.
            semantic_score = 0
            if query_vector is not None and job.vector_embedding is not None:
                # job.vector_embedding là Pickle, load ra thành array
                sim = self._cosine_similarity(query_vector, job.vector_embedding)
                semantic_score = sim * 100  # Quy đổi về thang 100

            # 3. Tính điểm tổng hợp (Hybrid Score)
            # Nếu job không có vector, fallback về keyword score hoàn toàn
            if semantic_score > 0:
                final_score = (keyword_score * 0.4) + (semantic_score * 0.6)
            else:
                final_score = keyword_score

            # Chỉ lấy job có độ phù hợp nhất định (> 30%)
            if final_score > 30:
                scored_jobs.append({
                    "title": job.title,
                    "company": job.company.name if job.company else "N/A",
                    "score": round(final_score, 1),
                    "salary_min": job.salary_min,
                    "salary_max": job.salary_max,
                    "matched_skills": list(matched),
                    "missing_skills": list(missing),
                    "reason": "Phù hợp ngữ nghĩa & kỹ năng" if semantic_score > 0 else "Phù hợp kỹ năng chuyên môn"
                })

        # Sắp xếp theo điểm cao nhất
        scored_jobs.sort(key=lambda x: x['score'], reverse=True)
        return scored_jobs[:limit]