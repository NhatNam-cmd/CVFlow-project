# app/services/ai_engine/gemini_client.py

import os
import json
import re
from google import genai
from google.genai import types


# --- PHẦN 1: CLASS MỚI (Dùng cho CVAnalyzer và code mới) ---
class GeminiClient:
    def __init__(self):
        # Ưu tiên lấy từ Config app (nếu có), không thì lấy biến môi trường
        api_key = os.environ.get("GOOGLE_API_KEY")

        if not api_key:
            print("⚠️ Cảnh báo: Chưa cấu hình GOOGLE_API_KEY")
            self.client = None
        else:
            try:
                # Cấu hình Client dùng API v1beta (như code cũ của bạn)
                self.client = genai.Client(
                    api_key=api_key,
                    http_options={"api_version": "v1beta"},
                )
            except Exception as e:
                print(f"❌ Lỗi khởi tạo Gemini Client: {e}")
                self.client = None

    def generate_text(self, prompt, temperature=0.7):
        """
        Trả về TEXT thô (Raw String).
        """
        if not self.client:
            return None

        # Logic thử nhiều model (Retry strategy)
        models_to_try = [
            "gemini-2.0-flash",
            "gemini-2.5-flash",
            "gemini-1.5-flash",
        ]

        errors = []
        for model_name in models_to_try:
            try:
                # print(f"🤖 [Class] Đang gọi model: {model_name}...")
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=temperature),
                )
                return response.text
            except Exception as e:
                errors.append(f"{model_name}: {str(e)}")
                continue

        print(f"❌ [Class] Thất bại toàn tập: {'; '.join(errors)}")
        return None

    def get_embedding(self, text):
        """
        Trả về Vector embedding
        """
        if not self.client:
            return None
        try:
            result = self.client.models.embed_content(
                model="models/text-embedding-004", contents=text
            )
            return result.embeddings[0].values
        except Exception as e:
            print(f"⚠️ [Class] Lỗi Embedding: {e}")
            return None


# --- PHẦN 2: CÁC HÀM CŨ (Wrapper để giữ tính năng cũ không chết) ---


def clean_json_string(json_str):
    """Hàm làm sạch JSON (giữ lại từ code cũ)"""
    if not json_str:
        return ""
    # Xóa markdown code block
    cleaned = re.sub(r"```json\s*|\s*```", "", json_str).strip()
    return cleaned


def call_gemini_pro(prompt):
    """
    Hàm cũ: Gọi Gemini và trả về JSON (Dictionary).
    Các chức năng HR cũ đang gọi hàm này.
    """
    client = GeminiClient()
    raw_text = client.generate_text(prompt)

    if raw_text:
        try:
            clean_text = clean_json_string(raw_text)
            return json.loads(clean_text)
        except json.JSONDecodeError:
            return {"error": "Lỗi AI trả về định dạng không phải JSON", "raw": raw_text}
    return {"error": "Lỗi kết nối AI"}


def get_text_embedding(text):
    """
    Hàm cũ: Lấy vector.
    Chức năng gợi ý Job đang gọi hàm này.
    """
    client = GeminiClient()
    return client.get_embedding(text)
