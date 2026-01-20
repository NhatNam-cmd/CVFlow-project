import re


class CVScorer:
    """
    Class này chấm điểm độ chuẩn của CV dựa trên logic cứng (ATS Friendly),
    không dùng AI để tránh ảo giác.
    """

    def __init__(self):
        self.SECTIONS = {
            "education": [
                "education",
                "học vấn",
                "trình độ học vấn",
                "đại học",
                "bằng cấp",
            ],
            "experience": [
                "experience",
                "kinh nghiệm",
                "làm việc",
                "work history",
                "employment",
            ],
            "skills": [
                "skills",
                "  kỹ năng",
                "chuyên môn",
                "technologies",
                "tech stack",
            ],
            "projects": ["projects", "dự án", "sản phẩm"],
            "contact": ["contact", "liên hệ", "thông tin"],
        }

        self.TECH_KEYWORDS = [
            "python",
            "java",
            "c++",
            "c#",
            "javascript",
            "html",
            "css",
            "react",
            "angular",
            "vue",
            "node",
            "sql",
            "mysql",
            "mongodb",
            "aws",
            "docker",
            "kubernetes",
            "git",
            "linux",
            "agile",
            "scrum",
            "machine learning",
            "ai",
        ]

    def evaluate(self, cv_obj):
        """
        Hàm evaluate thông minh, tự chọn chiến thuật chấm.
        Input: Đối tượng CV_File (Model)
        """
        if cv_obj.cv_source == "BUILDER" and cv_obj.structured_data:
            return self._evaluate_structured(cv_obj.structured_data)
        else:
            return self._evaluate_text(cv_obj.raw_text)

    def _evaluate_text(self, raw_text):
        if not raw_text:
            return 0, ["❌ Không đọc được nội dung text"]

        text_lower = raw_text.lower()
        score = 0
        details = []

        has_email = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text_lower)
        has_phone = re.search(r"\d{9,12}", text_lower)

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

        section_score = 0
        missing_sections = []

        if any(w in text_lower for w in self.SECTIONS["education"]):
            section_score += 10
        else:
            missing_sections.append("Học vấn")

        if any(w in text_lower for w in self.SECTIONS["experience"]):
            section_score += 10
        else:
            missing_sections.append("Kinh nghiệm làm việc")

        if any(w in text_lower for w in self.SECTIONS["skills"]):
            section_score += 10
        else:
            missing_sections.append("Kỹ năng")

        if any(w in text_lower for w in self.SECTIONS["projects"]):
            section_score += 10
        else:
            missing_sections.append("Dự án cá nhân/thực tế")

        score += section_score
        if not missing_sections:
            details.append("✅ Cấu trúc CV đầy đủ các phần quan trọng.")
        else:
            details.append(f"⚠️ Thiếu các mục quan trọng: {', '.join(missing_sections)}")

        word_count = len(text_lower.split())
        if 200 <= word_count <= 2000:
            score += 20
            details.append(f"✅ Độ dài tốt ({word_count} từ).")
        elif word_count < 200:
            score += 5
            details.append(f"⚠️ CV quá ngắn ({word_count} từ). Nên bổ sung chi tiết.")
        else:
            score += 10
            details.append(f"⚠️ CV hơi dài ({word_count} từ). Nên tóm tắt lại.")

        found_keywords = [kw for kw in self.TECH_KEYWORDS if kw in text_lower]
        unique_keywords = len(set(found_keywords))

        if unique_keywords >= 5:
            score += 20
            details.append(f"✅ Phát hiện {unique_keywords} từ khóa công nghệ (Tốt).")
        elif unique_keywords >= 1:
            score += 10
            details.append(
                f"⚠️ Hơi ít từ khóa công nghệ (chỉ thấy {unique_keywords} từ)."
            )
        else:
            details.append("❌ Không tìm thấy từ khóa kỹ thuật nào.")

        return score, details

    def _evaluate_structured(self, data):
        score = 0
        details = []

        p = data.get("personal", {})
        if p.get("email"):
            score += 10
            details.append("✅ Đã nhập Email.")
        else:
            details.append("❌ Thiếu Email.")

        if p.get("phone"):
            score += 10
            details.append("✅ Đã nhập SĐT.")
        else:
            details.append("❌ Thiếu SĐT.")

        edu = data.get("education", [])
        exp = data.get("experience", [])
        skills = data.get("skills", {})

        if len(edu) > 0:
            score += 10
            details.append("✅ Có thông tin Học vấn.")
        else:
            details.append("⚠️ Chưa nhập Học vấn.")

        if len(exp) > 0:
            score += 15
            details.append("✅ Có kinh nghiệm làm việc.")
        else:
            details.append("⚠️ Chưa nhập Kinh nghiệm.")

        h_skills = skills.get("hard_skills", [])
        s_skills = skills.get("soft_skills", [])
        if len(h_skills) > 0 or len(s_skills) > 0:
            score += 15
            details.append("✅ Có nhập Kỹ năng.")
        else:
            details.append("⚠️ Chưa nhập Kỹ năng.")

        summary = p.get("summary", "")
        if len(summary.split()) > 20:
            score += 10
            details.append("✅ Phần giới thiệu đủ chi tiết.")
        else:
            details.append("⚠️ Phần giới thiệu hơi ngắn.")

        good_exp = False
        if exp:
            good_exp = any(len(e.get("description", "").split()) > 10 for e in exp)

        if good_exp:
            score += 15
            details.append("✅ Mô tả kinh nghiệm chi tiết.")
        else:
            details.append("⚠️ Mô tả kinh nghiệm quá sơ sài.")

        all_skills_text = " ".join(h_skills).lower()
        found = [k for k in self.TECH_KEYWORDS if k in all_skills_text]
        if len(found) >= 3:
            score += 15
            details.append(f"✅ Kỹ năng chuyên môn tốt ({len(found)} công nghệ).")
        elif len(found) > 0:
            score += 10
            details.append("⚠️ Kỹ năng công nghệ hơi ít.")
        else:
            score += 5
            details.append("❌ Thiếu các từ khóa công nghệ phổ biến.")

        return min(100, score), details
