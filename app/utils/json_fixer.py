import json
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_and_parse_json(ai_response: str) -> dict:
    """
    Cố gắng sửa lỗi và trích xuất JSON từ câu trả lời của AI.
    Phiên bản nâng cao: Xử lý tốt hơn các trường hợp AI trả về text thừa.
    """
    try:
        return json.loads(ai_response)
    except json.JSONDecodeError:
        pass

    try:
        match = re.search(r"(\{.*\})", ai_response, re.DOTALL)

        if match:
            json_str = match.group(1)
            return json.loads(json_str)

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

    return {}
