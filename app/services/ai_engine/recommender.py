import numpy as np
import re
from datetime import datetime
from app.models import Job

# --- 1. CÁC HÀM PHỤ TRỢ (HELPER) ---


def cosine_similarity(vec_a, vec_b):
    """Tính độ tương đồng giữa 2 vector (Trả về 0.0 -> 1.0)"""
    if vec_a is None or vec_b is None:
        return 0.0

    # Chuyển về numpy array nếu chưa phải
    a = np.array(vec_a) if not isinstance(vec_a, np.ndarray) else vec_a
    b = np.array(vec_b) if not isinstance(vec_b, np.ndarray) else vec_b

    # Tính tích vô hướng và độ dài vector
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def calculate_years_from_json(experience_list):
    """Tính tổng số năm kinh nghiệm từ JSON (Giống hệt logic bên HR)"""
    total_months = 0
    current_date = datetime.now()

    if not experience_list:
        return 0

    for exp in experience_list:
        time_str = exp.get("time", "").lower()
        try:
            years = re.findall(r"\d{4}", time_str)
            start_year = int(years[0]) if years else current_date.year
            end_year = current_date.year

            if any(x in time_str for x in ["hiện tại", "present", "now", "nay"]):
                end_year = current_date.year
            elif len(years) >= 2:
                end_year = int(years[1])

            duration = end_year - start_year
            if duration == 0:
                duration = 0.5
            if duration < 0:
                duration = 0

            total_months += duration * 12
        except Exception:
            total_months += 6

    return round(total_months / 12, 1)


# --- 2. HÀM CHÍNH: GỢI Ý JOB ---


def recommend_jobs_for_cv(cv_obj, top_n=10):
    """
    Gợi ý Job dựa trên CV Object (Thay vì chỉ vector).
    Input: cv_obj (Model CV_File hoàn chỉnh)
    """
    # Lấy toàn bộ Job đang active và có vector
    jobs = Job.query.filter(
        Job.is_active == True, Job.vector_embedding.isnot(None)
    ).all()

    recommendations = []

    # Chuẩn bị dữ liệu CV một lần để đỡ lặp trong vòng for
    cv_vector = cv_obj.vector_embedding

    # Nếu là CV Builder, chuẩn bị sẵn Skill & Năm KN
    is_builder = cv_obj.cv_source == "BUILDER" and cv_obj.structured_data
    cv_skills = set()
    cv_years = 0

    if is_builder:
        cv_skills = set(
            [
                s.lower()
                for s in cv_obj.structured_data.get("skills", {}).get("hard_skills", [])
            ]
        )
        cv_years = calculate_years_from_json(
            cv_obj.structured_data.get("experience", [])
        )

    # --- VÒNG LẶP CHẤM ĐIỂM TỪNG JOB ---
    for job in jobs:
        # 1. Tính điểm Semantic (Luôn tính)
        semantic_score = 0
        if cv_vector and job.vector_embedding:
            similarity = cosine_similarity(cv_vector, job.vector_embedding)
            semantic_score = similarity * 100

        final_score = 0

        # 2. Phân nhánh tính điểm (Giống hệt HR)
        if is_builder:
            # === LOGIC CHO CV BUILDER ===

            # A. Chấm Skill (40%)
            job_skills = set()
            if job.structured_config and "hard_skills" in job.structured_config:
                job_skills = set(
                    [s.lower() for s in job.structured_config["hard_skills"]]
                )
            if job.skills_required:
                job_skills.update([s.lower().strip() for s in job.skills_required])

            skill_score = 0
            if len(job_skills) > 0:
                matched = job_skills.intersection(cv_skills)
                skill_score = (len(matched) / len(job_skills)) * 100
            else:
                skill_score = 100

            # B. Chấm Kinh nghiệm (30%)
            exp_score = 0
            req_years = job.min_years_experience or 0

            if req_years == 0:
                exp_score = 100
            elif cv_years >= req_years:
                exp_score = 100
            else:
                exp_score = (cv_years / req_years) * 100

            # C. Tổng hợp (Skill 40 - Exp 30 - Semantic 30)
            final_score = (
                (skill_score * 0.4) + (exp_score * 0.3) + (semantic_score * 0.3)
            )

        else:
            # === LOGIC CHO CV UPLOAD ===
            # Chỉ dùng Semantic
            final_score = semantic_score

        # 3. Lọc kết quả (Chỉ lấy job khớp > 15%)
        if final_score > 15:
            recommendations.append(
                {
                    "job": job,
                    "match_score": int(final_score),  # Làm tròn số nguyên
                    "semantic_only": int(semantic_score),  # Để debug nếu cần
                }
            )

    # 4. Sắp xếp giảm dần theo điểm
    recommendations.sort(key=lambda x: x["match_score"], reverse=True)

    return recommendations[:top_n]
