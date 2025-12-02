import logging
from app.services.pdf_parser import extract_text_from_pdf
from app.services.llm_engine import query_ollama_json, call_ollama
from app.prompts.templates import EXTRACT_INFO_PROMPT, SUMMARIZE_PROMPT
from app.repository import update_cv_data

# Import thư viện Vector (SBERT)
from sentence_transformers import SentenceTransformer

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


_vector_model = None


def get_vector_model():
    """
    Hàm Singleton để tải model.
    Chỉ tải model vào RAM khi được gọi lần đầu tiên.
    """
    global _vector_model  # Tham chiếu đến biến toàn cục ở trên

    if _vector_model is None:
        logger.info(
            """⏳ Initializing Embedding Model (SBERT)...
            This may take a while first time."""
        )
        try:
            # Load model (all-MiniLM-L6-v2 ~ 80MB)
            _vector_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("✅ Embedding Model Loaded Successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to load Embedding Model: {e}")
            raise e

    return _vector_model


def run_cv_processing(cv_id: int, file_path: str):
    """
    Quy trình xử lý CV End-to-End:
    1. Đọc text từ PDF
    2. Dùng AI trích xuất thông tin (JSON)
    3. Dùng AI tóm tắt
    4. Tạo Vector Embedding
    5. Lưu tất cả vào Database
    """
    logger.info(f"🚀 Processing CV ID: {cv_id}...")

    # 1. Module 1: Đọc file
    raw_text = extract_text_from_pdf(file_path)
    if not raw_text:
        logger.error("❌ Failed to extract text from PDF.")
        return False

    # In 100 ký tự đầu để debug xem đọc file có lỗi font không
    logger.info(f"📄 Raw Text Preview: {raw_text[:100]}...")

    # 2. Module 2: Trích xuất thông tin (JSON)
    # Dùng .replace() thay vì .format() để tránh lỗi dấu ngoặc nhọn JSON
    try:
        extract_prompt = EXTRACT_INFO_PROMPT.replace(
            "__CV_TEXT_PLACEHOLDER__", raw_text[:3000]
        )
        structured_data = query_ollama_json(extract_prompt)
        logger.info("✅ Extracted JSON Info")
    except Exception as e:
        logger.error(f"⚠️ Error extracting JSON: {e}")
        structured_data = {}

    # 3. Module 3: Tóm tắt
    try:
        summ_prompt = SUMMARIZE_PROMPT.replace(
            "__CV_TEXT_PLACEHOLDER__", raw_text[:3000]
        )
        summary = call_ollama(summ_prompt)
        logger.info("✅ Generated Summary")
    except Exception as e:
        logger.error(f"⚠️ Error summarizing: {e}")
        summary = ""

    # 4. Module 5: Tạo Vector (Embedding) - Lazy Loading
    vector = None
    try:
        # Gọi hàm get_vector_model() thay vì dùng biến trực tiếp
        model = get_vector_model()
        vector = model.encode(raw_text)
        logger.info("✅ Created Vector Embedding")
    except Exception as e:
        # Log lỗi nhưng không return False ngay, vẫn cho lưu các thông tin khác
        logger.error(f"❌ Error during vectorization: {e}")

    # 5. Lưu vào Database
    success = update_cv_data(cv_id, summary, structured_data, vector, raw_text)

    if success:
        logger.info(f"🎉 Successfully processed CV {cv_id}!")
    else:
        logger.error(f"❌ Failed to save data to DB for CV {cv_id}")

    return success
