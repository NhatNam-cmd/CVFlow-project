# app/services/scorer.py
# from typing import Any


def calculate_rule_based_score(
    cv_skills: list, job_requirements: str
) -> tuple[float, list[str]]:
    """
    Module 4: Chấm điểm dựa trên từ khóa (Rule-based).
    Input:
        - cv_skills: List kỹ năng từ AI (vd: ['Python', 'SQL', 'English'])
        - job_requirements: Text yêu cầu của Job (vd: "Yêu cầu Python, Django và SQL")
    Output:
        - Điểm số (0.0 - 100.0)
    """
    if not cv_skills or not job_requirements:
        return 0.0, []  # Trả về tuple

    req_text = job_requirements.lower()
    match_count = 0
    total_skills = len(cv_skills)
    matched_skills = []  # (+) List chứa các từ khóa trùng

    if total_skills == 0:
        return 0.0, []

    for skill in cv_skills:
        skill_str = str(skill)
        if skill_str.lower() in req_text:
            match_count += 1
            matched_skills.append(skill_str)  # (+) Lưu lại bằng chứng

    score = (match_count / total_skills) * 100

    # Trả về cả điểm và list từ khóa
    return min(100.0, round(score, 1)), matched_skills
