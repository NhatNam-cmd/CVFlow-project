import json
import re
import numpy as np
from app.services.ai_engine.gemini_client import GeminiClient
from app.services.ai_engine.prompts import (
    MATCHING_PROMPT_TEMPLATE,
    CV_REVIEW_PROMPT_TEMPLATE,
)


def extract_job_criteria(job_title, requirements_text):
    """
    Dùng AI để đọc Job Description và trích xuất ra JSON cấu trúc.
    """
    client = GeminiClient()
    prompt = f"""
    Bạn là trợ lý tuyển dụng AI. Nhiệm vụ của bạn là trích xuất thông tin từ yêu cầu công việc dưới đây thành JSON.

    ---
    VỊ TRÍ: {job_title}
    YÊU CẦU CHI TIẾT:
    "{requirements_text}"
    ---

    YÊU CẦU OUTPUT JSON (Tuyệt đối không dùng Markdown, chỉ trả về JSON thuần):
    {{
        "education_level": <string>, (Chỉ chọn 1 trong các giá trị: "University", "College", "Any")
        "hard_skills": [<list string>], (Trích xuất các kỹ năng chuyên môn, công nghệ)
        "soft_skills": [<list string>], (Trích xuất kỹ năng mềm)
        "benefits": [<list string>]
    }}
    Lưu ý: Nếu không tìm thấy thông tin thì để mảng rỗng [] hoặc "Any".
    """
    print("⚡ [AI] Đang trích xuất cấu trúc Job...")
    raw_text = client.generate_text(prompt)

    if raw_text:
        try:
            clean_json = re.sub(r"```json\s*|\s*```", "", raw_text).strip()
            start = clean_json.find("{")
            end = clean_json.rfind("}") + 1
            if start != -1 and end != -1:
                clean_json = clean_json[start:end]
            return json.loads(clean_json)
        except Exception as e:
            print(f"❌ Lỗi Parse JSON Job: {e}")
            return {}
    return {}


def review_cv_content(cv_text, source_type="Raw Text"):
    """
    Hàm Review CV (Logic mềm - Lời khuyên).
    """
    client = GeminiClient()
    if not cv_text or len(cv_text.strip()) < 10:
        return {"error": "Nội dung CV quá ngắn."}

    safe_text = cv_text[:12000]
    prompt = CV_REVIEW_PROMPT_TEMPLATE.format(
        cv_text=safe_text, source_type=source_type
    )

    print("🤖 [Core] Đang gửi Review CV...")
    raw_response = client.generate_text(prompt)

    if raw_response:
        try:
            clean_json = re.sub(r"```json\s*|\s*```", "", raw_response).strip()
            start = clean_json.find("{")
            end = clean_json.rfind("}") + 1
            if start != -1 and end != -1:
                clean_json = clean_json[start:end]

            data = json.loads(clean_json)

            if "pros" in data and "strengths" not in data:
                data["strengths"] = data.pop("pros")
            if "cons" in data and "weaknesses" not in data:
                data["weaknesses"] = data.pop("cons")

            return data
        except json.JSONDecodeError as e:
            print(f"❌ JSON Error: {e}")
            return {"error": "AI trả về dữ liệu lỗi."}
    else:
        return {"error": "Không kết nối được AI."}


class CVAnalyzer:
    def __init__(self):
        self.ai_client = GeminiClient()

    def calculate_cosine_similarity(self, vec_a, vec_b):
        """
        Tính độ tương đồng Cosine giữa 2 vector.
        """
        if not vec_a or not vec_b:
            return 0.0

        a = np.array(vec_a)
        b = np.array(vec_b)

        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def _build_scoring_prompt(self, job, cv):
        jd_context = f"""
        - Vị trí: {job.title}
        - Yêu cầu: {job.requirements}
        - Kỹ năng cần có: {job.skills_required}
        """
        cv_context = cv.raw_text[:10000] if cv.raw_text else "N/A"
        return MATCHING_PROMPT_TEMPLATE.format(jd_text=jd_context, cv_text=cv_context)

    def _parse_json_response(self, text):
        if not text:
            return None
        try:
            clean_text = re.sub(r"```json\s*|\s*```", "", text).strip()
            start = clean_text.find("{")
            end = clean_text.rfind("}") + 1
            if start != -1 and end != -1:
                clean_text = clean_text[start:end]
            return json.loads(clean_text)
        except Exception as e:
            print(f"🔥 JSON Error: {e}")
            return None
