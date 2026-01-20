# app/services/ai_engine/chatbot.py
from app.models.user import User
from app.services.ai_engine.gemini_client import GeminiClient
from app.services.ai_engine.prompts import CHATBOT_ADVISOR_PROMPT
from app.services.matching_service import JobMatcher


class CareerChatbot:
    def __init__(self):
        self.ai_client = GeminiClient()
        self.matcher = JobMatcher()

    def _format_job_list_for_ai(self, jobs_data):
        """
        Chuyển đổi list dictionary từ Matcher thành văn bản để AI đọc hiểu
        """
        if not jobs_data:
            return "Hệ thống đã quét nhưng chưa tìm thấy công việc phù hợp với yêu cầu này."

        text = ""
        for i, job in enumerate(jobs_data, 1):
            text += (
                f"{i}. {job['title']} (tại {job['company']})\n"
                f"   - Độ phù hợp: {job['score']}% ({job.get('reason', '')})\n"
                f"   - Lương: {job['salary_min']} - {job['salary_max']} triệu\n"
                f"   - Kỹ năng trùng khớp: {', '.join(job['matched_skills'])}\n\n"
            )
        return text

    def chat(self, user_id: int, user_message: str):
        user = User.query.get(user_id)
        if not user:
            return "Không tìm thấy thông tin người dùng."

        # 1. Phân tích ý định (Optional):
        # Nếu user message quá ngắn (ví dụ "Hi"), không nên dùng nó để search job.
        search_query = user_message if len(user_message.split()) > 3 else None

        # 2. Gọi Hybrid Matching (Truyền thêm search_query)
        # Logic mới: Nếu user hỏi "Tìm việc lương cao", matcher sẽ vector hóa câu đó để tìm job phù hợp.
        matched_jobs = self.matcher.find_top_matches(user_id, limit=3, user_query_text=search_query)

        # 3. Chuẩn bị dữ liệu cho Prompt
        # Lấy skill để AI biết background user
        # (Lưu ý: Logic lấy skill nên được đóng gói gọn, ở đây lấy tạm từ bio hoặc hàm helper cũ)
        user_skills_str = user.bio if user.bio else "Chưa cập nhật"

        job_list_text = self._format_job_list_for_ai(matched_jobs)

        # 4. Điền vào Prompt
        final_prompt = CHATBOT_ADVISOR_PROMPT.format(
            user_name=user.full_name,
            user_skills=user_skills_str,
            job_list_text=job_list_text,
            user_message=user_message
        )

        # 5. Gọi Gemini
        response = self.ai_client.generate_text(final_prompt)

        if not response:
            return "Xin lỗi, tôi đang gặp chút trục trặc kết nối. Bạn có thể hỏi lại sau được không?"

        return response