import json
import re
import numpy as np  # <--- Cần thêm thư viện này
from app import db
from app.models import Application, Job, CV_File
from app.services.ai_engine.gemini_client import GeminiClient
from app.services.ai_engine.prompts import MATCHING_PROMPT_TEMPLATE

class CVAnalyzer:
    def __init__(self):
        self.ai_client = GeminiClient()

    def calculate_cosine_similarity(self, vec_a, vec_b):
        """
        Tính độ tương đồng giữa 2 vector (Cosine Similarity).
        Kết quả từ -1 đến 1 (nhưng vector văn bản thường từ 0 đến 1).
        """
        if not vec_a or not vec_b:
            return 0.0

        # Chuyển list sang numpy array để tính toán
        a = np.array(vec_a)
        b = np.array(vec_b)

        # Tính dot product và norm (độ dài vector)
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

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

        # --- BƯỚC 1: ĐẢM BẢO DỮ LIỆU VECTOR (EMBEDDING) ---
        # Nếu Job chưa có vector (do job cũ tạo trước khi có tính năng này) -> Tạo ngay
        if not job.vector_embedding:
            print("⚡ Tạo Vector Embedding cho Job...")
            full_job_text = f"{job.title} . {job.requirements} . {job.skills_required}"
            job.vector_embedding = self.ai_client.get_embedding(full_job_text)
            db.session.commit()

        # Nếu CV chưa có vector -> Tạo ngay
        if not cv.vector_embedding:
            print("⚡ Tạo Vector Embedding cho CV...")
            # Nếu raw_text chưa có thì phải extract (logic này đã có ở route upload, đây chỉ là phòng hờ)
            if not cv.raw_text:
                print("⚠️ CV chưa có text, không thể tạo vector.")
            else:
                cv.vector_embedding = self.ai_client.get_embedding(cv.raw_text)
                db.session.commit()

        # --- BƯỚC 2: TÍNH ĐIỂM BẰNG TOÁN HỌC (CHÍNH XÁC 100%) ---
        math_score = 0
        if job.vector_embedding and cv.vector_embedding:
            similarity = self.calculate_cosine_similarity(job.vector_embedding, cv.vector_embedding)
            # Similarity thường trả về 0.0 -> 1.0. Nhân 100 để ra thang điểm.
            # Có thể nhân hệ số bias nếu muốn (VD: similarity * 100 sẽ hơi thấp, có thể * 1.2 nếu cần nới lỏng)
            math_score = round(similarity * 100, 1)
            print(f"🧮 Điểm toán học (Cosine Similarity): {math_score}")
        else:
            print("⚠️ Không thể tính điểm do thiếu vector.")

        # --- BƯỚC 3: DÙNG AI ĐỂ NHẬN XÉT (QUALITATIVE REVIEW) ---
        # Prompt bây giờ KHÔNG hỏi điểm số nữa, chỉ hỏi nhận xét
        prompt = self._build_scoring_prompt(job, cv)

        print("⏳ [DEBUG] Đang gửi prompt nhận xét lên Gemini...")
        ai_response = self.ai_client.generate_text(prompt)

        # Parse kết quả
        parsed_result = self._parse_json_response(ai_response)

        # --- BƯỚC 4: GỘP KẾT QUẢ ---
        if parsed_result:
            # Gán điểm toán học vào kết quả cuối cùng
            # Đây là bước quan trọng: Điểm số do code quy định, không phải do AI
            app.match_score = int(math_score)

            # Cập nhật JSON để lưu vào DB (ghi đè score của AI nếu lỡ AI có trả về)
            parsed_result["match_score"] = int(math_score)

            app.ai_analysis = parsed_result
            db.session.commit()
            print(f"✅ [Analyzer] XONG! Điểm chốt hạ: {app.match_score}/100")
        else:
            print("⚠️ [Analyzer] Lỗi đọc JSON từ AI.")

    def _build_scoring_prompt(self, job, cv):
        jd_context = f"""
        - Vị trí: {job.title}
        - Yêu cầu: {job.requirements}
        - Kỹ năng cần có: {job.skills_required}
        """
        cv_context = cv.raw_text[:8000] if cv.raw_text else "N/A"

        return MATCHING_PROMPT_TEMPLATE.format(jd_text=jd_context, cv_text=cv_context)

    def _parse_json_response(self, text):
        if not text: return None
        try:
            clean_text = re.sub(r"```json\s*|\s*```", "", text).strip()
            start = clean_text.find("{")
            end = clean_text.rfind("}") + 1
            if start != -1 and end != -1:
                clean_text = clean_text[start:end]
            return json.loads(clean_text)
        except Exception as e:
            print(f"🔥 JSON Error: {e}")
            return None