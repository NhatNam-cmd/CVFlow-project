import logging
from app.services.pdf_parser import extract_text_from_pdf
from app.services.llm_engine import query_ollama_json, call_ollama
from app.prompts.templates import EXTRACT_INFO_PROMPT, SUMMARIZE_PROMPT
from app.repository import update_cv_data
from app.services.scorer import calculate_rule_based_score  # (+) Import mới
from app.services.matcher import calculate_ai_match  # (+) Import mới
from app.repository import (
    get_job_by_id,
    update_score_result,
)  # (+) Cần thêm update_score_result vào repo

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


def run_cv_processing(cv_id: int, file_path: str, job_id: int):
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
    try:
        extract_prompt = EXTRACT_INFO_PROMPT.replace(
            "__CV_TEXT_PLACEHOLDER__", raw_text[:3000]
        )
        structured_data = query_ollama_json(extract_prompt)

        # 👇 [CODE MỚI] DỌN DẸP LIST SKILL (Flatten Skills) 👇
        # Mục đích: Biến ['Type: A, B', 'Type: C'] thành ['A', 'B', 'C']
        raw_skills = structured_data.get("skills", [])
        clean_skills = []

        if isinstance(raw_skills, list):
            for item in raw_skills:
                # 1. Bỏ các từ thừa như "Programming:", "Skills:", "- "
                item_str = (
                    str(item)
                    .replace("Programming:", "")
                    .replace("Cloud:", "")
                    .replace("Others:", "")
                    .replace("-", "")
                )

                # 2. Tách dấu phẩy (nếu AI gom chung một dòng)
                sub_items = item_str.split(",")

                for sub in sub_items:
                    clean_skill = sub.strip()  # Xóa khoảng trắng thừa
                    if clean_skill:
                        clean_skills.append(clean_skill)

        # Cập nhật lại list skill sạch vào data
        structured_data["skills"] = clean_skills
        # 👆 [KẾT THÚC CODE MỚI] 👆

        logger.info(f"✅ Extracted JSON Info: {len(clean_skills)} skills found.")

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
    try:
        # Lấy thông tin Job để so sánh
        job = get_job_by_id(job_id)

        if job:
            # A. Tạo Vector cho Job (nếu chưa có) - "Lazy Vectorization for Job"
            if job.vector_embedding is None and model:
                logger.info(f"⚡ Job {job_id} has no vector. Generating now...")
                job_vector = model.encode(job.description + " " + job.requirements)

            else:
                job_vector = job.vector_embedding

            # B. Tính điểm (Module 4 & 5)
            # Lấy list skill từ JSON (nếu có)
            candidate_skills = structured_data.get("skills", [])

            score_rule, matched_skills = calculate_rule_based_score(
                candidate_skills, job.requirements
            )
            score_ai = calculate_ai_match(vector, job_vector)

            # 3. (+) SINH CÂU GIẢI THÍCH TỰ ĐỘNG
            explanation_parts = []
            # Phần 1: Giải thích về từ khóa (Module 4)
            if matched_skills:
                skills_str = ", ".join(matched_skills[:5])  # Lấy tối đa 5 skill
                explanation_parts.append(
                    f"✅ <b>Keyword Match:</b> Found {len(matched_skills)} "
                    f"matching skills ({skills_str}...)."
                )
            else:
                explanation_parts.append(
                    "⚠️ <b>Keyword Match:</b> No direct keyword matches found."
                )

            # Phần 2: Giải thích về AI (Module 5)
            if score_ai >= 70:
                explanation_parts.append(
                    f"🔥 <b>AI Semantic:</b> High relevance ({score_ai}%). "
                    f"Context matches well."
                )
            elif score_ai >= 40:
                explanation_parts.append(
                    f"⚖️ <b>AI Semantic:</b> Moderate relevance ({score_ai}%)."
                )
            else:
                explanation_parts.append(
                    f"❄️ <b>AI Semantic:</b> Low relevance ({score_ai}%). "
                    f"Content seems unrelated."
                )

            final_explanation = "<br>".join(explanation_parts)

            # 4. Lưu vào DB (Truyền thêm final_explanation)
            update_score_result(cv_id, job_id, score_rule, score_ai, final_explanation)

            logger.info(f"🎯 Scores Calculated - Rule: {score_rule}, AI: {score_ai}")

            # C. Lưu điểm số vào bảng Score

    except Exception as e:
        logger.error(f"❌ Error during Scoring/Matching: {e}")
    # 5. Lưu vào Database
    success = update_cv_data(cv_id, summary, structured_data, vector, raw_text)

    if success:
        logger.info(f"🎉 Successfully processed CV {cv_id}!")
    else:
        logger.error(f"❌ Failed to save data to DB for CV {cv_id}")

    return success
