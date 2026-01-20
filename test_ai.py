import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    print("❌ Lỗi: Không tìm thấy GOOGLE_API_KEY trong file .env")
else:
    print(f"✅ Đã tìm thấy API Key: {api_key[:10]}...")
    genai.configure(api_key=api_key)

    print("\n🔍 Đang lấy danh sách Model hỗ trợ 'generateContent'...")
    try:
        found = False
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                print(f"   - {m.name}")
                found = True

        if not found:
            print(
                "⚠️ Không tìm thấy model nào hỗ trợ generateContent. Kiểm tra lại API Key."
            )
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
