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

        search_query = user_message if len(user_message.split()) > 3 else None

        matched_jobs = self.matcher.find_top_matches(
            user_id, limit=3, user_query_text=search_query
        )

        user_skills_str = user.bio if user.bio else "Chưa cập nhật"

        job_list_text = self._format_job_list_for_ai(matched_jobs)

        final_prompt = CHATBOT_ADVISOR_PROMPT.format(
            user_name=user.full_name,
            user_skills=user_skills_str,
            job_list_text=job_list_text,
            user_message=user_message,
        )

        response = self.ai_client.generate_text(final_prompt)

        if not response:
            return "Xin lỗi, tôi đang gặp chút trục trặc kết nối. Bạn có thể hỏi lại sau được không?"

        return response
