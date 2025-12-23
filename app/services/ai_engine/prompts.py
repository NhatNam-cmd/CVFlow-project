# services/ai_engine/prompts.py

MATCHING_PROMPT_TEMPLATE = """
Bạn là một Chuyên gia Tuyển dụng (HR Manager) kỳ cựu.
Hãy phân tích mức độ phù hợp giữa CV của ứng viên và Mô tả công việc (JD).

---
JD (MÔ TẢ CÔNG VIỆC):
{jd_text}

---
CV (HỒ SƠ ỨNG VIÊN):
{cv_text}

---
YÊU CẦU OUTPUT:
Hãy trả về kết quả dưới định dạng JSON thuần túy (không có markdown, không có ```json), bao gồm các trường sau:
1. "match_score": (Số nguyên từ 0-100) Đánh giá độ phù hợp.
2. "summary": (Chuỗi) Tóm tắt ngắn gọn nhận xét về ứng viên (bằng tiếng Việt).
3. "pros": (Mảng chuỗi) 3 điểm mạnh nổi bật khớp với JD (bằng tiếng Việt).
4. "cons": (Mảng chuỗi) 3 điểm yếu hoặc kỹ năng còn thiếu (bằng tiếng Việt).
5. "skills_matched": (Mảng chuỗi) Các kỹ năng chuyên môn có trong cả CV và JD.

Lưu ý: Hãy đánh giá khắt khe và công tâm.
"""
