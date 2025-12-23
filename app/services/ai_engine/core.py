# services/ai_engine/core.py
from .parser import extract_text_from_pdf
from .prompts import MATCHING_PROMPT_TEMPLATE
from .gemini_client import call_gemini_pro


def analyze_cv_matching(cv_path, jd_text):
    """
    Hàm chính để phân tích độ khớp giữa CV và JD.
    """
    # 1. Đọc nội dung CV từ file PDF
    cv_text = extract_text_from_pdf(cv_path)
    if not cv_text:
        return {"error": "Không thể đọc nội dung file CV"}

    # 2. Tạo prompt
    final_prompt = MATCHING_PROMPT_TEMPLATE.format(jd_text=jd_text, cv_text=cv_text)

    # 3. Gọi AI phân tích
    ai_result = call_gemini_pro(final_prompt)

    if not ai_result:
        return {"error": "Lỗi khi phân tích AI"}

    return ai_result
