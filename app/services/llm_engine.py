import requests
import json
import os
from typing import Dict, Any

# Lấy cấu hình từ biến môi trường (file .env)
OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = os.environ.get("LLM_MODEL", "llama3")


def call_ollama(prompt: str) -> str:
    """
    Hàm cốt lõi: Gửi prompt sang Ollama và nhận về text trả lời.
    """
    url = f"{OLLAMA_URL}/api/generate"
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,  # False để chờ nó viết xong mới trả về 1 cục
    }

    try:
        print(f"🤖 Calling Ollama ({MODEL_NAME})...")  # Log để biết đang chạy
        response = requests.post(url, json=payload, timeout=120)  # Timeout 2 phút
        response.raise_for_status()

        # Kết quả trả về nằm trong key 'response'
        return response.json().get("response", "")

    except requests.exceptions.ConnectionError:
        print(
            "❌ Lỗi: Không kết nối được với Ollama. Bạn đã bật 'ollama run llama3' chưa?"
        )
        return ""
    except Exception as e:
        print(f"❌ Lỗi gọi AI: {e}")
        return ""


# --- Hàm Wrapper để trả về JSON (Sẽ dùng cho Module 2) ---
def query_ollama_json(prompt: str) -> Dict[str, Any]:
    """
    Gửi prompt và cố gắng ép kiểu kết quả về JSON (Python Dict)
    """
    # Thêm câu lệnh ép buộc JSON vào prompt
    json_instruction = "\nIMPORTANT: Return ONLY valid JSON format. No explanations."
    full_response = call_ollama(prompt + json_instruction)

    # Đoạn này sau này chúng ta sẽ dùng 'json_fixer.py' để xử lý kỹ hơn
    # Tạm thời cứ thử parse đơn giản
    try:
        # Tìm dấu { đầu tiên và dấu } cuối cùng để cắt bớt lời dẫn thừa
        start = full_response.find("{")
        end = full_response.rfind("}") + 1
        if start != -1 and end != -1:
            json_str = full_response[start:end]
            return json.loads(json_str)
        else:
            return {}  # Không tìm thấy JSON
    except json.JSONDecodeError:
        print(f"⚠️ AI không trả về đúng JSON: {full_response[:100]}...")
        return {}
