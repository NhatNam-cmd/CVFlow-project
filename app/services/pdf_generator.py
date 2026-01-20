# app/services/pdf_generator.py
from fpdf import FPDF
from unidecode import unidecode


class PDFGenerator:
    @staticmethod
    def create_cv_pdf(data, output_path):
        """
        Tạo file PDF từ dữ liệu JSON.
        Sử dụng unidecode để chuyển tiếng Việt sang không dấu (tránh lỗi font khi demo).
        """
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Cấu hình Font mặc định (Arial)
        pdf.set_font("Arial", size=11)

        def txt(text):
            """Hàm clean text: Chuyển tiếng Việt có dấu -> không dấu"""
            if not text:
                return ""
            return unidecode(str(text))

        # --- 1. HEADER (Căn giữa) ---
        p = data.get("personal", {})
        pdf.set_font("Arial", "B", 24)
        pdf.cell(0, 15, txt(p.get("full_name", "Your Name")), ln=True, align="C")

        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(100, 100, 100)  # Màu xám
        pdf.cell(0, 10, txt(p.get("job_title", "")), ln=True, align="C")

        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(0, 0, 0)  # Về màu đen
        contact = (
            f"{txt(p.get('email'))} | {txt(p.get('phone'))} | {txt(p.get('address'))}"
        )
        pdf.cell(0, 8, contact, ln=True, align="C")

        if p.get("linkedin"):
            pdf.cell(0, 6, txt(p.get("linkedin")), ln=True, align="C")

        pdf.ln(10)  # Khoảng cách

        # Hàm vẽ tiêu đề mục
        def section_title(title):
            pdf.set_font("Arial", "B", 16)
            pdf.set_fill_color(240, 240, 240)  # Nền xám nhạt
            pdf.cell(0, 10, txt(title).upper(), ln=True, fill=True)
            pdf.ln(4)

        # --- 2. SUMMARY ---
        if p.get("summary"):
            section_title("Summary")
            pdf.set_font("Arial", "", 11)
            pdf.multi_cell(0, 6, txt(p.get("summary")))
            pdf.ln(8)

        # --- 3. SKILLS ---
        skills = data.get("skills", {})
        h_skills = skills.get("hard_skills", [])
        s_skills = skills.get("soft_skills", [])

        if h_skills or s_skills:
            section_title("Skills")
            pdf.set_font("Arial", "", 11)

            if h_skills:
                pdf.set_font("Arial", "B", 11)
                pdf.write(6, "Technical Skills: ")
                pdf.set_font("Arial", "", 11)
                pdf.write(6, txt(", ".join(h_skills)))
                pdf.ln(8)

            if s_skills:
                pdf.set_font("Arial", "B", 11)
                pdf.write(6, "Soft Skills: ")
                pdf.set_font("Arial", "", 11)
                pdf.write(6, txt(", ".join(s_skills)))
                pdf.ln(8)
            pdf.ln(4)

        # --- 4. EXPERIENCE ---
        exp_list = data.get("experience", [])
        if exp_list:
            section_title("Experience")
            for item in exp_list:
                # Dòng 1: Vị trí - Công ty
                pdf.set_font("Arial", "B", 12)
                title = f"{txt(item.get('position'))} at {txt(item.get('company'))}"
                pdf.cell(0, 7, title, ln=True)

                # Dòng 2: Thời gian (In nghiêng)
                pdf.set_font("Arial", "I", 10)
                pdf.set_text_color(80, 80, 80)
                pdf.cell(0, 6, txt(item.get("time")), ln=True)

                # Dòng 3: Mô tả
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Arial", "", 11)
                pdf.multi_cell(0, 6, txt(item.get("description")))
                pdf.ln(6)

        # --- 5. EDUCATION ---
        edu_list = data.get("education", [])
        if edu_list:
            section_title("Education")
            for item in edu_list:
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 7, txt(item.get("school")), ln=True)

                pdf.set_font("Arial", "", 11)
                detail = f"{txt(item.get('degree'))} ({txt(item.get('time'))})"
                pdf.cell(0, 6, detail, ln=True)
                pdf.ln(4)

        # Lưu file
        pdf.output(output_path)

    def _clean_text(text):
        """
        Hàm xử lý text để tránh lỗi font Latin-1 của FPDF.
        Thay thế các ký tự tiếng Việt thành không dấu hoặc tương đương để không crash.
        """
        if not text:
            return ""

        import unidecode

        return unidecode.unidecode(text)  # Chuyển "Tiếng Việt" -> "Tieng Viet"
