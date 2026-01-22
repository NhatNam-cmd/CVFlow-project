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
                "kỹ năng",
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
            "flask",
            "django",
            "spring",
        ]

    def evaluate(self, cv_obj):
        """
        Hàm evaluate thông minh, tự chọn chiến thuật chấm.
        Input: Đối tượng CV_File (Model)
        """
        # FIX LỖI QUAN TRỌNG:
        # Nếu là Builder, dù data rỗng {} hay None thì vẫn phải chấm theo kiểu Structured
        # Code cũ: if ... and cv_obj.structured_data (Nên nếu rỗng nó nhảy sang else -> lỗi)

        if cv_obj.cv_source == "BUILDER":
            data = cv_obj.structured_data if cv_obj.structured_data else {}
            return self._evaluate_structured(data)
        else:
            # Trường hợp PDF Upload
            return self._evaluate_text(cv_obj.raw_text)

    def _evaluate_text(self, raw_text):
        if not raw_text:
            return 0, ["❌ Không đọc được nội dung text từ file."]

        text_lower = raw_text.lower()
        score = 0
        details = []

        # 1. Check Email & Phone
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

        # 2. Check Sections
        section_score = 0
        missing_sections = []

        if any(w in text_lower for w in self.SECTIONS["education"]):
            section_score += 10
        else:
            missing_sections.append("Học vấn")

        if any(w in text_lower for w in self.SECTIONS["experience"]):
            section_score += 10
        else:
            missing_sections.append("Kinh nghiệm")

        if any(w in text_lower for w in self.SECTIONS["skills"]):
            section_score += 10
        else:
            missing_sections.append("Kỹ năng")

        if any(w in text_lower for w in self.SECTIONS["projects"]):
            section_score += 10
        else:
            missing_sections.append("Dự án")

        score += section_score
        if not missing_sections:
            details.append("✅ Cấu trúc CV đầy đủ.")
        else:
            details.append(f"⚠️ Thiếu các mục: {', '.join(missing_sections)}")

        # 3. Check Length
        word_count = len(text_lower.split())
        if 200 <= word_count <= 2000:
            score += 20
            details.append(f"✅ Độ dài tốt ({word_count} từ).")
        elif word_count < 200:
            score += 5
            details.append(f"⚠️ CV quá ngắn ({word_count} từ).")
        else:
            score += 10
            details.append(f"⚠️ CV hơi dài ({word_count} từ).")

        # 4. Check Keywords
        found_keywords = [kw for kw in self.TECH_KEYWORDS if kw in text_lower]
        unique_keywords = len(set(found_keywords))

        if unique_keywords >= 5:
            score += 20
            details.append(f"✅ Tìm thấy {unique_keywords} từ khóa công nghệ.")
        elif unique_keywords >= 1:
            score += 10
            details.append(f"⚠️ Hơi ít từ khóa công nghệ ({unique_keywords} từ).")
        else:
            details.append("❌ Không tìm thấy từ khóa kỹ thuật nào.")

        return min(100, score), details

    def _evaluate_structured(self, data):
        """
        Chấm điểm cho CV Builder (JSON)
        """
        score = 0
        details = []

        # Nếu data rỗng hoàn toàn (trường hợp user mới tạo chưa nhập gì)
        if not data:
            return 0, ["❌ CV chưa có dữ liệu nào. Vui lòng nhập thông tin."]

        p = data.get("personal", {})

        # 1. Kiểm tra Email (Có nội dung mới tính)
        if p.get("email") and p.get("email").strip():
            score += 10
            details.append("✅ Đã nhập Email.")
        else:
            details.append("❌ Thiếu Email.")

        # 2. Kiểm tra SĐT
        if p.get("phone") and p.get("phone").strip():
            score += 10
            details.append("✅ Đã nhập SĐT.")
        else:
            details.append("❌ Thiếu SĐT.")

        edu = data.get("education", [])
        exp = data.get("experience", [])
        skills = data.get("skills", {})

        # 3. Lọc bỏ các item rỗng trong danh sách Education
        valid_edu = [e for e in edu if e.get("school") and e.get("school").strip()]

        if len(valid_edu) > 0:
            score += 10
            details.append("✅ Có thông tin Học vấn.")
        else:
            details.append("⚠️ Chưa nhập Học vấn.")

        # 4. Lọc bỏ item rỗng trong Experience
        valid_exp = [
            e
            for e in exp
            if (e.get("company") and e.get("company").strip())
            or (e.get("position") and e.get("position").strip())
        ]

        if len(valid_exp) > 0:
            score += 15
            details.append("✅ Có kinh nghiệm làm việc.")
        else:
            details.append("⚠️ Chưa nhập Kinh nghiệm.")

        # 5. Kiểm tra Skills (Lọc rỗng)
        h_skills = [s for s in skills.get("hard_skills", []) if s.strip()]
        s_skills = [s for s in skills.get("soft_skills", []) if s.strip()]

        if len(h_skills) > 0 or len(s_skills) > 0:
            score += 15
            details.append("✅ Có nhập Kỹ năng.")
        else:
            details.append("⚠️ Chưa nhập Kỹ năng.")

        # 6. Kiểm tra Summary
        summary = p.get("summary", "")
        if summary and len(summary.split()) > 20:
            score += 10
            details.append("✅ Phần giới thiệu đủ chi tiết.")
        elif summary and len(summary.strip()) > 0:
            details.append("⚠️ Phần giới thiệu hơi ngắn.")
        else:
            # Không trừ điểm nếu không có, nhưng cũng không cộng
            pass

            # 7. Kiểm tra độ dài mô tả kinh nghiệm
        good_exp = False
        if valid_exp:
            good_exp = any(
                len(e.get("description", "").split()) > 10 for e in valid_exp
            )

        if good_exp:
            score += 15
            details.append("✅ Mô tả kinh nghiệm chi tiết.")
        elif valid_exp:
            details.append("⚠️ Mô tả kinh nghiệm quá sơ sài.")

        # 8. Check từ khóa công nghệ
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

        # ĐẢM BẢO LUÔN CÓ RETURN
        return min(100, score), details
