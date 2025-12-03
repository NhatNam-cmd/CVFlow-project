# app/services/matcher.py

from sentence_transformers import util
import logging

logger = logging.getLogger(__name__)


def calculate_ai_match(cv_vector, job_vector) -> float:
    """
    Module 5: So khớp ngữ nghĩa (Semantic Matching).
    Input:
        - cv_vector: Vector của CV (numpy array / tensor)
        - job_vector: Vector của Job Description
    Output:
        - Điểm số (0.0 - 100.0)
    """
    if cv_vector is None or job_vector is None:
        logger.warning("⚠️ One of the vectors is None. Cannot calculate match.")
        return 0.0

    try:
        # Sử dụng util.cos_sim của thư viện SBERT để tính Cosine Similarity
        # Kết quả trả về là một Tensor nằm trong khoảng [-1, 1]
        similarity = util.cos_sim(cv_vector, job_vector)

        # Lấy giá trị float ra khỏi Tensor
        score = similarity.item()

        # Chuẩn hóa: Cosine Sim thường từ 0 đến 1 (với văn bản).
        # Nhân 100 để ra thang điểm phần trăm.
        # Nếu score < 0 (rất hiếm với văn bản), coi là 0.
        final_score = max(0.0, score * 100)

        return round(final_score, 1)

    except Exception as e:
        logger.error(f"❌ Error calculating AI match: {e}")
        return 0.0
