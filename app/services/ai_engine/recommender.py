import numpy as np
from app.models import Job


def cosine_similarity(vec_a, vec_b):
    """Tính độ tương đồng giữa 2 vector (Trả về 0.0 -> 1.0)"""
    if vec_a is None or vec_b is None:
        return 0.0

    # Chuyển về numpy array
    a = np.array(vec_a)
    b = np.array(vec_b)

    # Tính tích vô hướng và độ dài vector
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def recommend_jobs_for_cv(cv_vector, top_n=10):
    """
    Gợi ý Job dựa trên vector của CV.
    """
    if not cv_vector:
        return []

    # 1. Lấy tất cả các Job đang active và ĐÃ CÓ vector
    # (Lưu ý: Với dữ liệu lớn hàng triệu dòng thì phải dùng pgvector,
    # nhưng với đồ án vài nghìn job thì load lên RAM tính vẫn nhanh chán)
    jobs = Job.query.filter(
        Job.is_active == True, Job.vector_embedding.isnot(None)
    ).all()

    recommendations = []

    # 2. Lặp qua từng job để tính điểm match
    for job in jobs:
        score = cosine_similarity(cv_vector, job.vector_embedding)

        # Chỉ lấy những job có độ khớp > 15% (cho đỡ rác)
        if score > 0.15:
            recommendations.append(
                {"job": job, "match_score": round(score * 100)}  # Đổi sang thang 100
            )

    # 3. Sắp xếp giảm dần theo điểm số
    recommendations.sort(key=lambda x: x["match_score"], reverse=True)

    return recommendations[:top_n]
