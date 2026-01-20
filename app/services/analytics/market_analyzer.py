import numpy as np
from app import db
from app.models import Job, MarketData, Application
from app.services.ai_engine.gemini_client import get_text_embedding
from sqlalchemy import func, or_
from datetime import datetime


class MarketAnalyzer:
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
        self.category_vectors = {}

    def analyze_and_save(self):
        """
        Hàm chính: Phân tích thị trường và lưu vào bảng MarketData (Breakdown theo Level)
        """
        if not self.category_vectors:
            self._preload_category_vectors()

        print("📊 Đang phân tích thị trường (Chi tiết Level)...")

        MarketData.query.delete()

        jobs = Job.query.filter_by(is_active=True).all()

        data_buckets = {}

        for job in jobs:
            standard_title = self._semantic_classify(job)

            level = job.level.upper() if job.level else "MIDDLE"
            if "SENIOR" in level:
                level = "SENIOR"
            elif "JUNIOR" in level:
                level = "JUNIOR"
            elif "FRESHER" in level or "INTERN" in level:
                level = "FRESHER"
            elif "LEAD" in level or "MANAGER" in level:
                level = "LEAD"
            else:
                level = "MIDDLE"

            key = (standard_title, level)

            if key not in data_buckets:
                data_buckets[key] = {"salaries": [], "skills": [], "job_count": 0}

            salary = job.salary_max if job.salary_max else job.salary_min
            if salary:
                data_buckets[key]["salaries"].append(salary)

            if job.skills_required:
                data_buckets[key]["skills"].extend(job.skills_required)

            data_buckets[key]["job_count"] += 1

        for (title, level), data in data_buckets.items():
            if not data["salaries"]:
                continue

            avg_salary = sum(data["salaries"]) / len(data["salaries"])
            top_skills = self._get_top_frequency(data["skills"], 5)

            demand_score = data["job_count"]

            report = MarketData(
                job_title_normalized=title,
                level=level,  # Lưu Level cụ thể
                avg_salary_min=0,
                avg_salary_max=avg_salary,
                demand_score=demand_score,
                top_skills=top_skills,
                updated_at=datetime.utcnow(),
            )
            db.session.add(report)

        db.session.commit()
        print("✅ Đã cập nhật Báo cáo thị trường.")

    def _preload_category_vectors(self):
        print("📥 Đang tạo vector cho danh mục chuẩn...")
        for cat in self.STANDARD_CATEGORIES:
            vec = get_text_embedding(cat)
            if vec:
                self.category_vectors[cat] = vec

    def _semantic_classify(self, job):
        """Phân loại Job dựa trên so khớp Vector"""
        if not job.vector_embedding:
            return "Uncategorized"

        job_vec = np.array(job.vector_embedding)
        best_match = "Other IT Jobs"
        highest_score = -1

        for cat, cat_vec in self.category_vectors.items():
            cat_vec_np = np.array(cat_vec)
            score = np.dot(job_vec, cat_vec_np) / (
                np.linalg.norm(job_vec) * np.linalg.norm(cat_vec_np)
            )

            if score > highest_score:
                highest_score = score
                best_match = cat

        if highest_score < 0.4:
            return "Other IT Jobs"

        return best_match

    def _get_top_frequency(self, items, top_n=5):
        from collections import Counter

        if not items:
            return []
        return [item[0] for item in Counter(items).most_common(top_n)]

    @staticmethod
    def get_rejection_stats(position_filter="All"):
        """
        Thống kê lý do từ chối (Static Method)
        """
        query = (
            db.session.query(Application.rejected_reason, func.count(Application.id))
            .join(Job)
            .filter(
                Application.status == "REJECTED",
                Application.rejected_reason is not None,
            )
        )

        if position_filter != "All":
            keywords = {
                "Python Developer": ["python", "django", "flask", "ai", "data"],
                "Java Developer": ["java", "spring", "j2ee"],
                "Frontend Developer": ["frontend", "react", "vue", "angular", "js"],
                "Backend Developer": [
                    "backend",
                    "node",
                    "php",
                    "golang",
                    "java",
                    "python",
                ],
                "DevOps / SRE": ["devops", "aws", "cloud", "docker"],
                "Tester / QA / QC": ["test", "qa", "qc"],
                "Data Scientist / AI": ["data", "ai", "learning"],
                "Fullstack Developer": ["fullstack", "node", "react", "vue"],
                "Mobile Developer": ["mobile", "android", "ios", "flutter"],
                "Business Analyst (BA)": ["ba", "analyst"],
                "Project Manager / PO": ["manager", "po", "product"],
            }

            search_terms = keywords.get(
                position_filter, [position_filter.split(" ")[0].lower()]
            )
            conditions = [Job.title.ilike(f"%{term}%") for term in search_terms]
            query = query.filter(or_(*conditions))

        results = query.group_by(Application.rejected_reason).all()
        return {r[0]: r[1] for r in results}
