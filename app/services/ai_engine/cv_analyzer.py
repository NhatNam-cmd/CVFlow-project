import json
import re
from app import db
from app.models import Application, Job, CV_File
from app.services.ai_engine.gemini_client import GeminiClient
from app.services.ai_engine.prompts import MATCHING_PROMPT_TEMPLATE


class CVAnalyzer:
    def __init__(self):
        self.ai_client = GeminiClient()

    def analyze_application(self, application_id, force_refresh=False):
        print(f"🤖 [Analyzer] Đang xử lý Application ID: {application_id}")

        app = Application.query.get(application_id)
        if not app:
            print("❌ App not found")
            return

        if app.ai_analysis and not force_refresh:
            print("✅ [Analyzer] Đã có kết quả cũ. Bỏ qua.")
            return

        job = Job.query.get(app.job_id)
        cv = CV_File.query.get(app.cv_id)

        if not job or not cv:
            print("❌ Dữ liệu Job hoặc CV bị thiếu.")
            return

        # 1. KIỂM TRA ĐẦU VÀO (QUAN TRỌNG)
        # Nếu raw_text rỗng -> AI sẽ không chấm được
        cv_text_len = len(cv.raw_text) if cv.raw_text else 0
        print(
            f"🔍 [DEBUG] Độ dài Job Requirements: {len(job.requirements) if job.requirements else 0}"
        )
        print(f"🔍 [DEBUG] Độ dài CV Raw Text: {cv_text_len}")

        if cv_text_len < 50:
            print(
                "⚠️ [WARNING] Nội dung CV quá ngắn hoặc chưa được parse! Điểm sẽ thấp."
            )

        # 2. Tạo Prompt
        prompt = self._build_scoring_prompt(job, cv)

        # 3. Gọi AI & Debug Response
        print("⏳ [DEBUG] Đang gửi prompt lên Gemini...")
        ai_response = self.ai_client.generate_text(prompt)

        # 👇 IN RA KẾT QUẢ THÔ TỪ AI ĐỂ SOI LỖI 👇
        print(f"📥 [DEBUG] AI Raw Response:\n{ai_response}")

        # 4. Parse JSON
        parsed_result = self._parse_json_response(ai_response)

        # 👇 IN RA KẾT QUẢ SAU KHI PARSE 👇
        print(f"🛠 [DEBUG] Parsed Result: {parsed_result}")

        if parsed_result:
            app.match_score = parsed_result.get("match_score", 0)
            app.ai_analysis = parsed_result

            db.session.commit()
            print(f"✅ [Analyzer] XONG! Điểm: {app.match_score}/100")
        else:
            print("⚠️ [Analyzer] Lỗi đọc JSON (Parsed Result is None).")

    def _build_scoring_prompt(self, job, cv):
        jd_context = f"""
        - Vị trí: {job.title}
        - Yêu cầu: {job.requirements}
        - Kỹ năng: {job.skills_required}
        """
        # Nếu CV rỗng thì ghi N/A để AI biết
        cv_context = cv.raw_text[:4000] if cv.raw_text else "N/A (Empty Content)"

        return MATCHING_PROMPT_TEMPLATE.format(jd_text=jd_context, cv_text=cv_context)

    def _parse_json_response(self, text):
        if not text:
            return None
        try:
            # Xử lý Markdown code block ```json ... ```
            clean_text = re.sub(r"```json\s*|\s*```", "", text).strip()

            # Tìm biên giới của JSON object { ... }
            start = clean_text.find("{")
            end = clean_text.rfind("}") + 1
            if start != -1 and end != -1:
                clean_text = clean_text[start:end]

            return json.loads(clean_text)
        except Exception as e:
            print(f"🔥 [PARSE ERROR] Không thể đọc JSON: {e}")
            print(f"   Dữ liệu gây lỗi: {text}")
            # Trả về mặc định 0 điểm để không crash
            return {
                "match_score": 0,
                "summary": "Lỗi định dạng dữ liệu từ AI.",
                "pros": [],
                "cons": [],
                "skills_matched": [],
            }
