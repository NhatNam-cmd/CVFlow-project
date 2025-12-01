from app.services.pdf_parser import extract_text_from_pdf
from app.services.llm_engine import call_ollama
from app.prompts.templates import EXTRACT_INFO_PROMPT, SUMMARIZE_PROMPT
from app.repository import update_cv_data
from app.utils.json_fixer import clean_and_parse_json

# Import thư viện Vector (SBERT)
from sentence_transformers import SentenceTransformer

# import os

# Tải model Vector (chỉ tải 1 lần khi khởi động app)
# Model 'all-MiniLM-L6-v2' rất nhẹ và nhanh
print("⏳ Loading Embedding Model (SBERT)...")
vector_model = SentenceTransformer("all-MiniLM-L6-v2")
print("✅ Embedding Model Loaded!")


def run_cv_processing(cv_id: int, file_path: str):
    """
    Quy trình xử lý CV End-to-End:
    1. Đọc text từ PDF
    2. Dùng AI trích xuất thông tin (JSON)
    3. Dùng AI tóm tắt
    4. Tạo Vector Embedding
    5. Lưu tất cả vào Database
    """
    print(f"🚀 Processing CV ID: {cv_id}...")

    # 1. Module 1: Đọc file
    raw_text = extract_text_from_pdf(file_path)
    if not raw_text:
        print("❌ Failed to extract text from PDF.")
        return False

    # 2. Module 2: Trích xuất thông tin (JSON)
    # Gắn text vào prompt mẫu
    extract_prompt = EXTRACT_INFO_PROMPT.format(
        cv_text=raw_text[:3000]
    )  # Cắt bớt nếu quá dài
    raw_json_str = call_ollama(extract_prompt)  # Gọi AI
    structured_data = clean_and_parse_json(raw_json_str)  # Làm sạch JSON
    print("✅ Extracted JSON Info")

    # 3. Module 3: Tóm tắt
    # Đơn giản là nối prompt tóm tắt với text
    summ_prompt = f"{SUMMARIZE_PROMPT}\nOriginal Text: {raw_text[:3000]}"
    summary = call_ollama(summ_prompt)
    print("✅ Generated Summary")

    # 4. Module 5: Tạo Vector (Embedding)
    vector = vector_model.encode(raw_text)
    print("✅ Created Vector Embedding")

    # 5. Lưu vào Database
    success = update_cv_data(cv_id, summary, structured_data, vector)

    if success:
        print(f"🎉 Successfully processed CV {cv_id}!")
    else:
        print(f"❌ Failed to save data to DB for CV {cv_id}")

    return success
