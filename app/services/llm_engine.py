import requests
import os
from typing import Dict, Any

# (+) Import hàm sửa lỗi JSON mới từ utils
from app.utils.json_fixer import clean_and_parse_json

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


# --- Hàm Wrapper để trả về JSON (Đã nâng cấp) ---
def query_ollama_json(prompt: str) -> Dict[str, Any]:
    """
    Gửi prompt và ép kiểu kết quả về JSON sử dụng json_fixer mạnh mẽ hơn.
    """
    # Thêm câu lệnh ép buộc JSON vào prompt
    json_instruction = "\nIMPORTANT: Return ONLY valid JSON format. No explanations."
    full_response = call_ollama(prompt + json_instruction)

    # (+) Thay thế logic thủ công cũ bằng hàm chuyên dụng
    # Hàm này sẽ tự lo liệu việc cắt chuỗi, xóa Markdown, bắt lỗi...
    return clean_and_parse_json(full_response)
