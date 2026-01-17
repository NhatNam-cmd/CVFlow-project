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
            return "Hiện tại hệ thống chưa tìm thấy công việc nào khớp với kỹ năng của bạn."

        text = ""
        for i, job in enumerate(jobs_data, 1):
            text += (
                f"{i}. {job['title']} (tại {job['company']})\n"
                f"   - Độ phù hợp: {job['score']}%\n"
                f"   - Lương: {job['salary_min']} - {job['salary_max']} triệu\n"
                f"   - Kỹ năng bạn đã có: {', '.join(job['matched_skills'])}\n"
                f"   - Kỹ năng bạn CẦN HỌC THÊM: {', '.join(job['missing_skills'])}\n\n"
            )
        return text

    def chat(self, user_id: int, user_message: str):
        # 1. Lấy thông tin User
        user = User.query.get(user_id)
        if not user:
            return "Không tìm thấy thông tin người dùng."

        # 2. Gọi Python Logic để tìm việc (Core Feature)
        matched_jobs = self.matcher.find_top_matches(user_id)

        # 3. Chuẩn bị dữ liệu cho AI
        user_skills_list = list(self.matcher.get_user_skills(user))
        user_skills_str = ", ".join(user_skills_list) if user_skills_list else "Chưa cập nhật (hãy cập nhật Bio)"
        job_list_text = self._format_job_list_for_ai(matched_jobs)

        # 4. Điền vào Prompt
        final_prompt = CHATBOT_ADVISOR_PROMPT.format(
            user_name=user.full_name,
            user_skills=user_skills_str,
            job_list_text=job_list_text,
            user_message=user_message
        )

        # 5. Gọi Gemini để sinh câu trả lời tự nhiên
        # Lưu ý: Hàm generate_text trả về string
        response = self.ai_client.generate_text(final_prompt)

        if not response:
            return "Xin lỗi, hệ thống AI đang bận. Nhưng dựa vào dữ liệu, tôi thấy bạn nên xem qua các công việc Python Developer."

        return response