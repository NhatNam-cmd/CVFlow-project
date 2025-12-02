from app.services.pdf_parser import extract_text_from_pdf
from app.services.llm_engine import call_ollama
from app.prompts.templates import EXTRACT_INFO_PROMPT, SUMMARIZE_PROMPT
from app.repository import update_cv_data
from app.utils.json_fixer import clean_and_parse_json

# Import thư viện Vector (SBERT)
import logging
from sentence_transformers import SentenceTransformer

# import os

# Tải model Vector (chỉ tải 1 lần khi khởi động app)
# Model 'all-MiniLM-L6-v2' rất nhẹ và nhanh
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("⏳ Loading Embedding Model (SBERT)...")
vector_model = SentenceTransformer("all-MiniLM-L6-v2")
print("✅ Embedding Model Loaded!")


def get_vector_model():
    global _vector_model
    if _vector_model is None:
        logger.info(
            """⏳ Initializing Embedding Model (SBERT)...
            This may take a while first time."""
        )
        try:
            # Chỉ thực sự load model khi hàm này được gọi lần đầu
            _vector_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("✅ Embedding Model Loaded Successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to load Embedding Model: {e}")
            raise e  # Ném lỗi để dừng quy trình nếu model hỏng

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
        print("❌ Failed to extract text from PDF.")
        return False

    # 2. Module 2: Trích xuất thông tin (JSON)
    # Gắn text vào prompt mẫu
    extract_prompt = EXTRACT_INFO_PROMPT.replace(
        "__CV_TEXT_PLACEHOLDER__", raw_text[:3000]
    )  # Cắt bớt nếu quá dài
    raw_json_str = call_ollama(extract_prompt)  # Gọi AI
    structured_data = clean_and_parse_json(raw_json_str)  # Làm sạch JSON
    print("✅ Extracted JSON Info")

    # 3. Module 3: Tóm tắt
    # Đơn giản là nối prompt tóm tắt với text
    summ_prompt = SUMMARIZE_PROMPT.replace("__CV_TEXT_PLACEHOLDER__", raw_text[:3000])
    summary = call_ollama(summ_prompt)
    print("✅ Generated Summary")

    # 4. Module 5: Tạo Vector (Embedding)
    try:
        # [SỬA] Gọi hàm get_vector_model() thay vì dùng biến trực tiếp
        model = get_vector_model()
        vector = model.encode(raw_text)
        logger.info("✅ Created Vector Embedding")
    except Exception as e:
        logger.error(f"❌ Error during vectorization: {e}")
        return False

    # 5. Lưu vào Database
    success = update_cv_data(cv_id, summary, structured_data, vector, raw_text)

    if success:
        print(f"🎉 Successfully processed CV {cv_id}!")
    else:
        print(f"❌ Failed to save data to DB for CV {cv_id}")

    return success
