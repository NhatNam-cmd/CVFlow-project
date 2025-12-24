# app/services/ai_engine/gemini_client.py
import os
import json
from google import genai
from google.genai import types

# 1. Cấu hình Client dùng API v1beta (BẮT BUỘC cho model 2.0/2.5)
try:
    client = genai.Client(
        api_key=os.environ.get("GOOGLE_API_KEY"),
        http_options={"api_version": "v1beta"},  # <--- THÊM DÒNG NÀY
    )
except Exception as e:
    print(f"Lỗi khởi tạo Gemini Client: {e}")
    client = None


def clean_json_string(json_str):
    if not json_str:
        return ""
    return json_str.replace("```json", "").replace("```", "").strip()


def call_gemini_pro(prompt):
    if not client:
        return {"error": "Lỗi Client chưa được khởi tạo."}

    # 2. Cập nhật danh sách model theo đúng cái bạn ĐANG CÓ (Dựa trên log bạn gửi lúc nãy)
    models_to_try = [
        "gemini-2.0-flash",  # Ưu tiên 1: Bạn có model này
        "gemini-2.5-flash",  # Ưu tiên 2: Bạn cũng có model này
        "gemini-1.5-flash",  # Dự phòng: Bản chuẩn quốc dân
    ]

    errors = []

    for model_name in models_to_try:
        try:
            print(f"🤖 Đang thử gọi model: {model_name}...")

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.7),
            )

            result_text = response.text
            clean_text = clean_json_string(result_text)
            return json.loads(clean_text)

        except Exception as e:
            print(f"⚠️ Lỗi với {model_name}: {e}")
            errors.append(f"{model_name}: {str(e)}")
            continue

            # In ra tất cả lỗi để dễ debug hơn
    return {"error": f"Thất bại toàn tập. Chi tiết lỗi: {'; '.join(errors)}"}


def get_text_embedding(text):
    """
    Chuyển đổi văn bản thành Vector (Embedding) sử dụng model text-embedding-004
    """
    if not client:
        return None

    try:
        # Model embedding chuẩn của Google
        result = client.models.embed_content(
            model="models/text-embedding-004", contents=text
        )
        # Trả về list số thực (Vector)
        return result.embeddings[0].values
    except Exception as e:
        print(f"⚠️ Lỗi Embedding: {e}")
        return None
