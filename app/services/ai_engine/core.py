# services/ai_engine/core.py
from .prompts import MATCHING_PROMPT_TEMPLATE, CV_REVIEW_PROMPT_TEMPLATE
from .gemini_client import call_gemini_pro
from .parser import extract_text_from_pdf
from app.services.ai_engine.gemini_client import GeminiClient
import json
import re



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
    Hàm này gửi CV lên AI để lấy nhận xét (Lời khuyên),
    KHÔNG dùng để chấm điểm (điểm số đã tính bằng thuật toán).
    """
    client = GeminiClient()

    # 1. Kiểm tra đầu vào
    if not cv_text or len(cv_text.strip()) < 10:
        return {"error": "Nội dung CV quá ngắn hoặc không đọc được."}

    # 2. Tạo Prompt
    # Cắt ngắn text nếu quá dài để tránh lỗi token limit (Gemini chịu được ~30k token, nhưng cứ cắt cho an toàn)
    safe_text = cv_text[:10000]
    prompt = CV_REVIEW_PROMPT_TEMPLATE.format(cv_text=safe_text)

    # 3. Gọi AI
    print("🤖 [Core] Đang gửi yêu cầu Review CV sang Gemini...")
    raw_response = client.generate_text(prompt)

    # 4. Parse JSON kết quả
    if raw_response:
        try:
            # Làm sạch chuỗi JSON (xóa markdown ```json ... ```)
            clean_json = re.sub(r"```json\s*|\s*```", "", raw_response).strip()

            # Tìm điểm bắt đầu và kết thúc của JSON object
            start = clean_json.find("{")
            end = clean_json.rfind("}") + 1
            if start != -1 and end != -1:
                clean_json = clean_json[start:end]

            data = json.loads(clean_json)
            return data

        except json.JSONDecodeError as e:
            print(f"❌ [Core] Lỗi Parse JSON từ AI: {e}")
            print(f"   Raw Response: {raw_response}")
            return {"error": "AI trả về dữ liệu lỗi, vui lòng thử lại."}
    else:
        return {"error": "Không kết nối được với AI Service."}