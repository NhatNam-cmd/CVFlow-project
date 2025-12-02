import json
import re
import logging

# Cấu hình logging để debug dễ hơn
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_and_parse_json(ai_response: str) -> dict:
    """
    Cố gắng sửa lỗi và trích xuất JSON từ câu trả lời của AI.
    Phiên bản nâng cao: Xử lý tốt hơn các trường hợp AI trả về text thừa.
    """
    # 1. Thử parse trực tiếp (trường hợp lý tưởng)
    try:
        return json.loads(ai_response)
    except json.JSONDecodeError:
        pass

    try:
        # 2. Tìm đoạn JSON hợp lệ đầu tiên trong chuỗi
        # Regex này tìm chuỗi bắt đầu bằng { và kết thúc bằng } (không tham lam)
        # DOTALL giúp dấu chấm (.) khớp cả ký tự xuống dòng
        match = re.search(r"(\{.*\})", ai_response, re.DOTALL)

        if match:
            json_str = match.group(1)
            # Xóa các ký tự xuống dòng thừa, tab thừa có thể gây lỗi
            # Nhưng cẩn thận không xóa khoảng trắng trong value
            # Tạm thời chỉ thử load đoạn tìm được
            return json.loads(json_str)

        # 3. Trường hợp AI trả về Markdown code block (```json ... ```)
        code_block_match = re.search(
            r"```json\s*(\{.*?\})\s*```", ai_response, re.DOTALL
        )
        if code_block_match:
            return json.loads(code_block_match.group(1))

    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Failed to parse JSON from AI response: {e}")
        logger.debug(
            f"Raw AI Response: {ai_response}"
        )  # Log ra để xem AI trả về cái gì mà lỗi

    # 4. Nếu bó tay, trả về dict rỗng để code không crash
    return {}
