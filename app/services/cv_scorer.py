import re

class CVScorer:
    """
    Class này chấm điểm độ chuẩn của CV dựa trên logic cứng (ATS Friendly),
    không dùng AI để tránh ảo giác.
    """

    def __init__(self):
        # Các từ khóa để nhận diện các mục chính (Hỗ trợ cả Anh và Việt)
        self.SECTIONS = {
            "education": ["education", "học vấn", "trình độ học vấn", "đại học", "bằng cấp"],
            "experience": ["experience", "kinh nghiệm", "làm việc", "work history", "employment"],
            "skills": ["skills", "kỹ năng", "chuyên môn", "technologies", "tech stack"],
            "projects": ["projects", "dự án", "sản phẩm"],
            "contact": ["contact", "liên hệ", "thông tin"]
        }

        # Danh sách từ khóa Tech phổ biến (để check xem có phải CV IT không)
        self.TECH_KEYWORDS = [
            "python", "java", "c++", "c#", "javascript", "html", "css", "react",
            "angular", "vue", "node", "sql", "mysql", "mongodb", "aws", "docker",
            "kubernetes", "git", "linux", "agile", "scrum", "machine learning", "ai"
        ]

    def evaluate(self, raw_text):
        if not raw_text:
            return 0, {"error": "Không đọc được nội dung text"}

        text_lower = raw_text.lower()
        score = 0
        details = []

        # 1. KIỂM TRA THÔNG TIN LIÊN HỆ (20 điểm)
        # Regex tìm email
        has_email = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text_lower)
        # Regex tìm số điện thoại (đơn giản)
        has_phone = re.search(r'\d{9,12}', text_lower)

        if has_email:
            score += 10
            details.append("✅ Đã có Email.")
        else:
            details.append("❌ Thiếu Email liên hệ.")

        if has_phone:
            score += 10
            details.append("✅ Đã có Số điện thoại.")
        else:
            details.append("❌ Thiếu Số điện thoại.")

        # 2. KIỂM TRA CẤU TRÚC (40 điểm - Mỗi mục 10 điểm)
        section_score = 0
        missing_sections = []

        # Kiểm tra Education
        if any(w in text_lower for w in self.SECTIONS["education"]):
            section_score += 10
        else:
            missing_sections.append("Học vấn")

        # Kiểm tra Experience
        if any(w in text_lower for w in self.SECTIONS["experience"]):
            section_score += 10
        else:
            missing_sections.append("Kinh nghiệm làm việc")

        # Kiểm tra Skills
        if any(w in text_lower for w in self.SECTIONS["skills"]):
            section_score += 10
        else:
            missing_sections.append("Kỹ năng")

        # Kiểm tra Projects
        if any(w in text_lower for w in self.SECTIONS["projects"]):
            section_score += 10
        else:
            missing_sections.append("Dự án cá nhân/thực tế")

        score += section_score
        if not missing_sections:
            details.append("✅ Cấu trúc CV đầy đủ các phần quan trọng.")
        else:
            details.append(f"⚠️ Thiếu các mục quan trọng: {', '.join(missing_sections)}")

        # 3. KIỂM TRA ĐỘ DÀI (20 điểm)
        word_count = len(text_lower.split())
        if 200 <= word_count <= 2000:
            score += 20
            details.append(f"✅ Độ dài tốt ({word_count} từ).")
        elif word_count < 200:
            score += 5 # Cho điểm vớt
            details.append(f"⚠️ CV quá ngắn ({word_count} từ). Nên bổ sung chi tiết.")
        else:
            score += 10
            details.append(f"⚠️ CV hơi dài ({word_count} từ). Nên tóm tắt lại.")

        # 4. KIỂM TRA TỪ KHÓA CÔNG NGHỆ (20 điểm)
        # Tìm xem có bao nhiêu từ khóa tech xuất hiện
        found_keywords = [kw for kw in self.TECH_KEYWORDS if kw in text_lower]
        unique_keywords = len(set(found_keywords))

        if unique_keywords >= 5:
            score += 20
            details.append(f"✅ Phát hiện {unique_keywords} từ khóa công nghệ (Tốt).")
        elif unique_keywords >= 1:
            score += 10
            details.append(f"⚠️ Hơi ít từ khóa công nghệ (chỉ thấy {unique_keywords} từ).")
        else:
            details.append("❌ Không tìm thấy từ khóa kỹ thuật nào. CV này có đúng ngành IT không?")

        return score, details