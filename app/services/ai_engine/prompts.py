MATCHING_PROMPT_TEMPLATE = """
Bạn là một Chuyên gia Tuyển dụng (HR Manager) khắt khe.
Nhiệm vụ của bạn là SO SÁNH nội dung CV và JD để đưa ra nhận xét chi tiết.
(Lưu ý: Không cần chấm điểm số, điểm số sẽ được tính toán riêng).

---
JD (MÔ TẢ CÔNG VIỆC):
{jd_text}

---
CV (HỒ SƠ ỨNG VIÊN):
{cv_text}

---
YÊU CẦU OUTPUT:
Hãy trả về kết quả dưới định dạng JSON thuần túy (không markdown), bao gồm các trường sau:
1. "summary": (Chuỗi) Tóm tắt mức độ phù hợp của ứng viên (khoảng 2-3 câu ngắn gọn).
2. "pros": (Mảng chuỗi) 3 điểm mạnh nhất của ứng viên so với JD này.
3. "cons": (Mảng chuỗi) 3 điểm yếu hoặc kỹ năng quan trọng mà ứng viên còn thiếu.
4. "skills_matched": (Mảng chuỗi) Liệt kê các kỹ năng chuyên môn (Hard Skills) tìm thấy trong cả CV và JD.

Lưu ý:
- Trả lời hoàn toàn bằng Tiếng Việt.
- Phân tích dựa trên sự thật (fact-based).
"""

CV_REVIEW_PROMPT_TEMPLATE = """
Bạn là Chuyên gia Tư vấn Nghề nghiệp (Career Coach).
Hãy phân tích CV dưới đây (được trích xuất từ {source_type}) và đưa ra nhận xét.

---
NỘI DUNG CV:
{cv_text}

---
YÊU CẦU OUTPUT JSON:
Hãy trả về JSON thuần túy gồm 4 trường sau (Tiếng Việt):
1. "summary": (String) Nhận xét tổng quan (ngắn gọn, súc tích).
2. "strengths": (Array) 3 điểm mạnh nổi bật nhất của hồ sơ này.
3. "weaknesses": (Array) 3 điểm yếu cần khắc phục.
4. "improvements": (Array) 3 lời khuyên cụ thể để cải thiện.

Lưu ý:
- Nếu CV quá sơ sài, hãy thẳng thắn góp ý trong phần weaknesses.
- Trả về JSON hợp lệ, không markdown.
"""
