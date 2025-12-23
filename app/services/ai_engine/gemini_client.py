# services/ai_engine/gemini_client.py
import os
import json
import google.generativeai as genai

# Cấu hình API Key
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))


def clean_json_string(json_str):
    """Làm sạch chuỗi JSON"""
    json_str = json_str.replace("```json", "").replace("```", "").strip()
    return json_str


def call_gemini_pro(prompt):
    """
    Gửi prompt lên Gemini và nhận về JSON.
    """
    # 👇 CẬP NHẬT DANH SÁCH MODEL DỰA TRÊN LIST BẠN GỬI
    models_to_try = [
        "gemini-2.5-flash",  # Ưu tiên 1: Bản mới nhất, nhanh nhất
        "gemini-2.5-pro",  # Ưu tiên 2: Nếu cần suy luận sâu hơn (nhưng chậm hơn)
        "gemini-2.0-flash",  # Fallback: Bản ổn định đời trước
        "gemini-flash-latest",  # Fallback: Alias chung
    ]

    last_error = None

    for model_name in models_to_try:
        try:
            # print(f"🤖 Đang thử gọi model: {model_name}...") # Có thể bỏ comment để debug
            model = genai.GenerativeModel(model_name)

            # Gọi hàm generate
            response = model.generate_content(prompt)

            result_text = response.text

            # Parse sang JSON object
            clean_text = clean_json_string(result_text)
            return json.loads(clean_text)

        except Exception as e:
            # print(f"⚠️ Lỗi với {model_name}: {e}")
            last_error = e
            continue  # Thử model tiếp theo trong danh sách

    # Nếu thử hết mà vẫn lỗi
    error_msg = f"Tất cả các model đều thất bại. Lỗi cuối cùng: {str(last_error)}"
    print(error_msg)
    return {"error": error_msg}
