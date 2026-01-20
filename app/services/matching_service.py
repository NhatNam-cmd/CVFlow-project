from app.models.job import Job
from app.models.user import User
from sqlalchemy import or_


class JobMatcher:
    """
    Class này chịu trách nhiệm tính toán độ phù hợp giữa Ứng viên và Công việc
    bằng thuật toán Python thuần túy, không dùng AI.
    """

    def _normalize_skills(self, skills_input):
        """
        Helper function: Chuẩn hóa danh sách kỹ năng về chữ thường để so sánh.
        Input có thể là list hoặc string phân cách bằng dấu phẩy.
        """
        if not skills_input:
            return set()

        if isinstance(skills_input, str):
            # Tách chuỗi "Python, SQL, Flask" -> {"python", "sql", "flask"}
            return set(s.strip().lower() for s in skills_input.split(','))

        if isinstance(skills_input, list):
            return set(s.strip().lower() for s in skills_input)

        return set()

    def calculate_match_score(self, user_skills: set, job_skills: set) -> dict:
        """
        Tính điểm phù hợp (0-100%)
        Logic: (Số kỹ năng trùng / Tổng kỹ năng công việc yêu cầu) * 100
        """
        if not job_skills:
            return {"score": 0, "matched": [], "missing": []}

        # Python Set Operations: Giao (Intersection) và Hiệu (Difference)
        matched = user_skills.intersection(job_skills)
        missing = job_skills.difference(user_skills)

        score = (len(matched) / len(job_skills)) * 100

        return {
            "score": round(score, 1),
            "matched": list(matched),
            "missing": list(missing)
        }

    def get_user_skills(self, user: User):
        """
        Lấy kỹ năng của user.
        Lưu ý: Vì model User hiện tại chưa có cột 'skills',
        ta sẽ tạm thời trích xuất từ cột 'bio' hoặc trả về list mặc định để test.
        """
        # TODO: Sau này bạn nên thêm bảng CandidateSkill hoặc cột skills (JSON) vào User
        if user.bio:
            # Giả định user viết skill trong bio cách nhau dấu phẩy
            return self._normalize_skills(user.bio)
        return set()

    def find_top_matches(self, user_id: int, limit=3):
        """
        Hàm chính: Tìm job phù hợp nhất cho user
        """
        user = User.query.get(user_id)
        if not user:
            return []

        user_skills = self.get_user_skills(user)

        # 1. Lấy tất cả job đang active từ DB
        # Tối ưu: Chỉ lấy job chưa hết hạn (bạn có thể thêm filter ngày tháng)
        all_jobs = Job.query.filter_by(is_active=True).all()

        scored_jobs = []

        # 2. Loop & Scoring (Xử lý logic)
        for job in all_jobs:
            # Job.skills_required là cột JSON
            job_skills = self._normalize_skills(job.skills_required)

            result = self.calculate_match_score(user_skills, job_skills)

            # Chỉ lấy công việc có điểm phù hợp > 0 (hoặc ngưỡng bạn muốn)
            if result['score'] >= 0:
                scored_jobs.append({
                    "job_id": job.id,
                    "title": job.title,
                    "company": job.company.name if job.company else "Ẩn danh",
                    "salary_min": job.salary_min,
                    "salary_max": job.salary_max,
                    "score": result['score'],
                    "matched_skills": result['matched'],
                    "missing_skills": result['missing']
                })

        # 3. Sorting (Sắp xếp bằng Lambda function)
        # Sắp xếp giảm dần theo score
        scored_jobs.sort(key=lambda x: x['score'], reverse=True)

        return scored_jobs[:limit]