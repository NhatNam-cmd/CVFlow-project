# app/services/matching_service.py
import numpy as np
import pickle
from sqlalchemy import cast, or_, func
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, TEXT

from app.models.job import Job
from app.models.user import User
from app.models.application import CV_File
from app.services.ai_engine.gemini_client import GeminiClient


class JobMatcher:
    def __init__(self):
        self.ai_client = GeminiClient()

    def _normalize_skills(self, skills_input):
        """Chuẩn hóa kỹ năng về dạng set chữ thường"""
        if not skills_input:
            return set()

        normalized = set()
        if isinstance(skills_input, str):
            normalized = set(s.strip().lower() for s in skills_input.split(',') if s.strip())
        elif isinstance(skills_input, (list, set, tuple)):
            for s in skills_input:
                if isinstance(s, str) and s.strip():
                    normalized.add(s.strip().lower())
        return normalized

    def _get_user_skills_strategy(self, user):
        """Lấy skills ưu tiên từ CV > Bio"""
        extracted_skills = set()

        # 1. Tìm CV chính
        main_cv = CV_File.query.filter_by(user_id=user.id, is_main=True).first()
        if main_cv and main_cv.structured_data:
            data = main_cv.structured_data
            raw_skills = data.get("skills", {})
            if isinstance(raw_skills, dict):
                extracted_skills.update(raw_skills.get("hard_skills", []))
                extracted_skills.update(raw_skills.get("soft_skills", []))
                extracted_skills.update(raw_skills.get("tools", []))
            elif isinstance(raw_skills, list):
                extracted_skills.update(raw_skills)

        # 2. Fallback Bio
        final_skills = self._normalize_skills(extracted_skills)
        if not final_skills and user.bio:
            final_skills = self._normalize_skills(user.bio)

        print(f"🔍 [Matcher] User Skills (Normalized): {final_skills}")  # DEBUG
        return final_skills

    def _cosine_similarity(self, vec_a, vec_b):
        if vec_a is None or vec_b is None:
            return 0.0
        a = np.array(vec_a)
        b = np.array(vec_b)
        if a.shape != b.shape:
            return 0.0
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def get_user_profile_vector(self, user):
        main_cv = CV_File.query.filter_by(user_id=user.id, is_main=True).first()
        if main_cv and main_cv.vector_embedding:
            return main_cv.vector_embedding
        if user.bio:
            return self.ai_client.get_embedding(user.bio)
        return None

    def find_top_matches(self, user_id: int, limit=5, user_query_text=None):
        user = User.query.get(user_id)
        if not user:
            return []

        user_skills = self._get_user_skills_strategy(user)

        # Query Vector
        if user_query_text:
            query_vector = self.ai_client.get_embedding(user_query_text)
        else:
            query_vector = self.get_user_profile_vector(user)

        # --- SỬA ĐỔI QUAN TRỌNG: NỚI LỎNG SQL FILTER ---
        # Thay vì dùng toán tử ?| (dễ sai Case), ta lấy Top 100 job active
        # và để Python xử lý việc so khớp chính xác.
        candidates = Job.query.filter_by(is_active=True).order_by(Job.created_at.desc()).limit(100).all()

        print(f"🔍 [Matcher] Found {len(candidates)} candidates from DB to scan.")  # DEBUG

        scored_jobs = []

        for job in candidates:
            # 1. Keyword Score (40%)
            job_skills = self._normalize_skills(job.skills_required)
            matched = user_skills.intersection(job_skills)

            keyword_score = 0
            if len(job_skills) > 0:
                keyword_score = (len(matched) / len(job_skills)) * 100

            # 2. Semantic Score (60%)
            semantic_score = 0
            if query_vector is not None and job.vector_embedding is not None:
                sim = self._cosine_similarity(query_vector, job.vector_embedding)
                semantic_score = sim * 100

            # 3. Final Score
            if semantic_score > 0:
                final_score = (keyword_score * 0.4) + (semantic_score * 0.6)
            else:
                final_score = keyword_score  # Nếu không có vector, dùng 100% điểm keyword

            # DEBUG LOGGING
            if final_score > 0:
                print(
                    f"   -> Job: {job.title} | Key: {keyword_score:.1f} | Sem: {semantic_score:.1f} | Final: {final_score:.1f}")

            # --- SỬA ĐỔI: HẠ NGƯỠNG LỌC XUỐNG 10 (DEBUG) ---
            if final_score > 10:
                scored_jobs.append({
                    "title": job.title,
                    "company": job.company.name if job.company else "N/A",
                    "score": round(final_score, 1),
                    "salary_min": job.salary_min,
                    "salary_max": job.salary_max,
                    "matched_skills": list(matched),
                    "missing_skills": list(job_skills.difference(user_skills)),
                    "reason": "Phù hợp ngữ nghĩa & chuyên môn" if semantic_score > 0 else "Phù hợp từ khóa kỹ năng"
                })

        scored_jobs.sort(key=lambda x: x['score'], reverse=True)
        return scored_jobs[:limit]