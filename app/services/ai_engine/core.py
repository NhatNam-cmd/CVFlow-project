# services/ai_engine/core.py
from .prompts import MATCHING_PROMPT_TEMPLATE, CV_REVIEW_PROMPT_TEMPLATE
from .gemini_client import call_gemini_pro
from .parser import extract_text_from_pdf


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


def review_cv_content(cv_text):
    """
    Chấm điểm và nhận xét CV dựa trên nội dung text.
    """
    if not cv_text or len(cv_text) < 50:
        return {"error": "Nội dung CV quá ngắn hoặc không đọc được."}

    # 1. Ghép prompt
    final_prompt = CV_REVIEW_PROMPT_TEMPLATE.format(cv_text=cv_text)

    # 2. Gọi AI
    ai_result = call_gemini_pro(final_prompt)

    return ai_result
