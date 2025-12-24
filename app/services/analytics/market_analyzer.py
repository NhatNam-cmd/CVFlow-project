import numpy as np
from app import db
from app.models import Job, MarketData, Application
from app.services.ai_engine.gemini_client import get_text_embedding
from sqlalchemy import func
from datetime import datetime


class MarketAnalyzer:
    # Danh sách các nhóm chuẩn mà chúng ta muốn thống kê
    STANDARD_CATEGORIES = [
        "Backend Developer",
        "Frontend Developer",
        "Fullstack Developer",
        "Mobile Developer",
        "DevOps / SRE",
        "Data Scientist / AI",
        "Tester / QA / QC",
        "Project Manager / PO",
        "System Admin / Network",
        "Business Analyst (BA)",
    ]

    def __init__(self):
        # Cache vector của các nhóm chuẩn để không phải gọi API nhiều lần
        self.category_vectors = {}

    def _preload_category_vectors(self):
        """Tạo vector cho các nhóm chuẩn ngay khi khởi tạo class"""
        print("📥 Đang tạo vector cho danh mục chuẩn...")
        for cat in self.STANDARD_CATEGORIES:
            vec = get_text_embedding(cat)
            if vec:
                self.category_vectors[cat] = vec

    def analyze_and_save(self):
        if not self.category_vectors:
            self._preload_category_vectors()
        print("📊 Đang phân tích thị trường bằng AI Semantic Matching...")

        # 1. Xóa dữ liệu cũ
        MarketData.query.delete()

        # 2. Lấy job active
        jobs = Job.query.filter_by(is_active=True).all()

        data_buckets = {}  # { 'Backend Developer': {'salaries': [], ...} }

        for job in jobs:
            # --- BƯỚC QUAN TRỌNG: DÙNG VECTOR ĐỂ PHÂN LOẠI ---
            standard_title = self._semantic_classify(job)

            if standard_title not in data_buckets:
                data_buckets[standard_title] = {
                    "salaries": [],
                    "skills": [],
                    "count": 0,
                }

            # Gom dữ liệu
            # Ưu tiên lấy max salary để báo cáo cho hấp dẫn, hoặc lấy trung bình của min-max
            salary = job.salary_max if job.salary_max else job.salary_min
            if salary:
                data_buckets[standard_title]["salaries"].append(salary)

            if job.skills_required:
                data_buckets[standard_title]["skills"].extend(job.skills_required)

            data_buckets[standard_title]["count"] += 1

        # 3. Lưu vào DB
        for title, data in data_buckets.items():
            if not data["salaries"]:
                continue

            avg_salary = sum(data["salaries"]) / len(data["salaries"])
            top_skills = self._get_top_frequency(data["skills"], 5)

            # Demand score: normalize theo số lượng job nhiều nhất
            max_job_count = (
                max([d["count"] for d in data_buckets.values()]) if data_buckets else 1
            )
            demand_score = int((data["count"] / max_job_count) * 100)

            report = MarketData(
                job_title_normalized=title,
                level="ALL",
                avg_salary_min=0,
                avg_salary_max=avg_salary,
                demand_score=demand_score,
                top_skills=top_skills,
                updated_at=datetime.utcnow(),
            )
            db.session.add(report)

        db.session.commit()
        print("✅ Đã cập nhật Báo cáo thị trường (AI Semantic).")

    def _semantic_classify(self, job):
        """
        Phân loại Job dựa trên so khớp Vector
        """
        # Nếu Job chưa có vector (do lỗi gì đó), fallback về rule-based hoặc tạo vector ngay
        if not job.vector_embedding:
            # Fallback đơn giản hoặc gọi API tạo vector ngay tại đây (tùy chọn)
            return "Uncategorized"

        job_vec = np.array(job.vector_embedding)
        best_match = "Uncategorized"
        highest_score = -1

        # So sánh vector job với từng vector category
        for cat, cat_vec in self.category_vectors.items():
            cat_vec_np = np.array(cat_vec)

            # Tính Cosine Similarity
            score = np.dot(job_vec, cat_vec_np) / (
                np.linalg.norm(job_vec) * np.linalg.norm(cat_vec_np)
            )

            if score > highest_score:
                highest_score = score
                best_match = cat

        # Ngưỡng chấp nhận (ví dụ > 0.4 mới tính, ko thì cho vào nhóm Khác)
        if highest_score < 0.4:
            return "Other IT Jobs"

        return best_match

    @staticmethod
    def get_rejection_stats():
        results = (
            db.session.query(Application.rejected_reason, func.count(Application.id))
            .filter(
                Application.status == "REJECTED",
                Application.rejected_reason is not None,
            )
            .group_by(Application.rejected_reason)
            .all()
        )
        return {r[0]: r[1] for r in results}

    def _get_top_frequency(self, items, top_n=5):
        from collections import Counter

        if not items:
            return []
        return [item[0] for item in Counter(items).most_common(top_n)]
