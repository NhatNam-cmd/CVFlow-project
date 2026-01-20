# app/services/cv_analyzer.py

import json
import re
import os
import numpy as np
from datetime import datetime
from flask import current_app

from app import db
from app.models import Application, Job, CV_File
from app.services.ai_engine.gemini_client import GeminiClient
from app.services.ai_engine.prompts import MATCHING_PROMPT_TEMPLATE

# 👇 QUAN TRỌNG: Import hàm đọc PDF có sẵn của bạn
from app.services.ai_engine.parser import extract_text_from_pdf


class CVAnalyzer:
    def __init__(self):
        self.ai_client = GeminiClient()

    def calculate_cosine_similarity(self, vec_a, vec_b):
        """
        Tính độ tương đồng Cosine giữa 2 vector.
        """
        if not vec_a or not vec_b:
            return 0.0

        a = np.array(vec_a)
        b = np.array(vec_b)

        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def _calculate_total_years(self, experience_list):
        """
        Tính tổng số năm kinh nghiệm từ danh sách các công việc.
        """
        total_months = 0
        current_date = datetime.now()

        for exp in experience_list:
            # Lấy chuỗi thời gian, ví dụ: "01/2020 - 05/2022" hoặc "Jun 2021 - Present"
            time_str = exp.get("time", "").lower()
            try:
                # Tìm tất cả các năm (4 chữ số) trong chuỗi
                years = re.findall(r"\d{4}", time_str)

                start_year = int(years[0]) if years else current_date.year
                end_year = current_date.year  # Mặc định là năm nay

                # Xử lý ngày kết thúc
                if any(x in time_str for x in ["hiện tại", "present", "now", "nay"]):
                    end_year = current_date.year
                elif len(years) >= 2:
                    end_year = int(years[1])

                # Tính khoảng cách
                duration = end_year - start_year

                # Logic bù trừ: Nếu làm cùng năm (2022-2022) tính là 0.5 năm
                if duration == 0:
                    duration = 0.5
                if duration < 0:
                    duration = 0  # Tránh lỗi nhập sai

                total_months += duration * 12

            except Exception:
                # Nếu format lạ quá không parse được, mặc định cộng 6 tháng an ủi
                total_months += 6

        return round(total_months / 12, 1)  # Trả về số năm (VD: 2.5)

    def analyze_application(self, application_id, force_refresh=False):
        """
        Hàm cốt lõi: So khớp CV và Job để chấm điểm.
        """
        print(f"🤖 [CVAnalyzer] Đang xử lý Application ID: {application_id}")

        # 1. Lấy dữ liệu từ DB
        app = Application.query.get(application_id)
        if not app:
            print("❌ App not found")
            return

        if app.ai_analysis and not force_refresh:
            print("✅ [CVAnalyzer] Đã có kết quả cũ. Bỏ qua.")
            return

        job = Job.query.get(app.job_id)
        cv = CV_File.query.get(app.cv_id)

        if not job or not cv:
            print("❌ Dữ liệu Job hoặc CV bị thiếu.")
            return

        # 2. Chuẩn bị Vector cho Job
        if not job.vector_embedding:
            print("⚡ Tạo Vector Embedding cho Job...")
            full_job_text = f"{job.title} . {job.requirements} . {job.skills_required}"
            job.vector_embedding = self.ai_client.get_embedding(full_job_text)
            db.session.commit()

        # 3. Chuẩn bị Vector cho CV (Bao gồm logic Tự phục hồi)
        if not cv.vector_embedding:
            print("⚡ Tạo Vector Embedding cho CV...")

            # 👇 LOGIC TỰ PHỤC HỒI: Nếu chưa có text -> Gọi parser đọc file PDF
            if not cv.raw_text:
                print("⚠️ CV chưa có text. Đang thử trích xuất từ file PDF gốc...")
                try:
                    # Tạo đường dẫn file vật lý
                    file_path = os.path.join(
                        current_app.config["UPLOAD_FOLDER"], cv.file_url
                    )

                    if os.path.exists(file_path):
                        # Gọi hàm parser của bạn
                        extracted_text = extract_text_from_pdf(file_path)

                        if extracted_text and len(extracted_text) > 10:
                            cv.raw_text = extracted_text
                            db.session.commit()
                            print("✅ Đã trích xuất text thành công!")
                        else:
                            print("❌ File PDF rỗng hoặc không đọc được text.")
                    else:
                        print(f"❌ Không tìm thấy file tại: {file_path}")
                except Exception as e:
                    print(f"❌ Lỗi khi đọc PDF: {e}")

            # Sau khi cố gắng trích xuất, nếu có text thì tạo vector
            if cv.raw_text:
                cv.vector_embedding = self.ai_client.get_embedding(cv.raw_text)
                db.session.commit()
            else:
                print("⚠️ Vẫn không có text -> Không thể tạo vector (Điểm sẽ là 0).")

        # =========================================================
        # 4. TÍNH TOÁN ĐIỂM SỐ
        # =========================================================

        final_score = 0
        semantic_score = 0
        breakdown = {}

        # Tính Semantic Score (AI Vector)
        if job.vector_embedding and cv.vector_embedding:
            similarity = self.calculate_cosine_similarity(
                job.vector_embedding, cv.vector_embedding
            )
            semantic_score = round(similarity * 100, 1)

        # --- PHÂN NHÁNH LOGIC: BUILDER vs UPLOAD ---
        if cv.cv_source == "BUILDER" and cv.structured_data:
            print("🔍 [CVAnalyzer] Đang chấm điểm theo cấu trúc (CV Builder)...")

            # A. Chấm điểm Kỹ năng (40%)
            job_skills = set()
            if job.structured_config and "hard_skills" in job.structured_config:
                job_skills = set(
                    [s.lower() for s in job.structured_config["hard_skills"]]
                )
            if job.skills_required:
                job_skills.update([s.lower().strip() for s in job.skills_required])

            cv_skills = set(
                [
                    s.lower()
                    for s in cv.structured_data.get("skills", {}).get("hard_skills", [])
                ]
            )

            skill_score = 0
            if len(job_skills) > 0:
                matched_skills = job_skills.intersection(cv_skills)
                skill_score = (len(matched_skills) / len(job_skills)) * 100
            else:
                skill_score = 100

                # B. Chấm điểm Kinh nghiệm (30%) - Dựa trên SỐ NĂM
            exp_score = 0
            req_exp_years = job.min_years_experience
            actual_exp_years = self._calculate_total_years(
                cv.structured_data.get("experience", [])
            )

            if req_exp_years == 0:
                exp_score = 100
            else:
                if actual_exp_years >= req_exp_years:
                    exp_score = 100
                else:
                    # Công thức tuyến tính
                    exp_score = (actual_exp_years / req_exp_years) * 100

            # C. Tổng hợp điểm
            final_score = (
                (skill_score * 0.4) + (exp_score * 0.3) + (semantic_score * 0.3)
            )

            breakdown = {
                "skill_score": int(skill_score),
                "exp_score": int(exp_score),
                "details": {
                    "matched_count": len(matched_skills) if len(job_skills) > 0 else 0,
                    "total_req": len(job_skills),
                    "actual_exp_years": actual_exp_years,
                    "req_exp_years": req_exp_years,
                },
            }

        else:
            # --- CV UPLOAD ---
            print("📄 [CVAnalyzer] Đang chấm điểm theo ngữ nghĩa (CV Upload)...")
            # Với CV Upload, điểm số chính là Semantic Score
            final_score = semantic_score
            breakdown = {
                "note": "Chấm điểm dựa trên phân tích ngữ nghĩa vector (Semantic Search).",
                "semantic_score": semantic_score,
            }

        # 5. GỬI PROMPT NHẬN XÉT (QUALITATIVE REVIEW)
        prompt = self._build_scoring_prompt(job, cv)
        print("⏳ [CVAnalyzer] Đang gửi prompt nhận xét lên Gemini...")

        # Gọi AI để lấy text nhận xét
        ai_response_text = self.ai_client.generate_text(prompt)
        parsed_result = self._parse_json_response(ai_response_text)

        if parsed_result:
            # 6. LƯU KẾT QUẢ VÀO DB
            app.match_score = int(final_score)

            parsed_result["match_score"] = int(final_score)
            parsed_result["semantic_score"] = int(semantic_score)
            parsed_result["breakdown"] = breakdown

            app.ai_analysis = parsed_result
            db.session.commit()
            print(f"✅ [CVAnalyzer] XONG! Điểm chốt hạ: {app.match_score}/100")
        else:
            print("⚠️ [CVAnalyzer] Lỗi đọc JSON từ AI.")

    def _build_scoring_prompt(self, job, cv):
        jd_context = f"""
        - Vị trí: {job.title}
        - Yêu cầu: {job.requirements}
        - Kỹ năng cần có: {job.skills_required}
        """
        # Lấy raw_text, nếu không có thì ghi chú
        cv_context = (
            cv.raw_text[:12000]
            if cv.raw_text
            else "Không có nội dung text (Lỗi đọc file)."
        )
        return MATCHING_PROMPT_TEMPLATE.format(jd_text=jd_context, cv_text=cv_context)

    def _parse_json_response(self, text):
        if not text:
            return None
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
