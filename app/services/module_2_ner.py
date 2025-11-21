"""
module_2_ner.py

Module 2 - Trích xuất thông tin (NER) từ văn bản thô.

Yêu cầu từ CVFlow:
- Nhận raw text từ Module 1.
- Trích xuất các thực thể quan trọng: Tên, Email, SĐT, Kỹ năng.
- Email & Phone dùng regex.
- Skills dùng danh sách từ khóa (keyword dictionary).
- Name dùng heuristic đơn giản từ header CV.
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

# Tải tokenizer nếu chưa có
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")


# Regex cho email & số điện thoại
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_PATTERN = re.compile(r"(\+?\d[\d\s\-]{7,14}\d)")

# Danh sách từ khóa kỹ năng
SKILL_KEYWORDS = {
    "python", "java", "javascript", "sql", "mysql", "html", "css",
    "react", "docker", "git", "linux", "pandas", "numpy",
    "machine learning", "deep learning", "nlp",
}


@dataclass
class ExtractedEntities:
    """Định dạng dữ liệu trả về từ Module 2."""
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    skills: List[str]

    def to_dict(self) -> Dict:
        """Trả về dạng dictionary để dễ lưu vào DB hoặc API."""
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "skills": self.skills,
        }


def _extract_email(text: str) -> Optional[str]:
    """Tìm email trong văn bản thô."""
    match = EMAIL_PATTERN.search(text)
    return match.group(0) if match else None


def _extract_phone(text: str) -> Optional[str]:
    """Tìm số điện thoại trong văn bản."""
    match = PHONE_PATTERN.search(text)
    return match.group(0) if match else None


def _extract_name(text: str) -> Optional[str]:
    """
    Dự đoán tên ứng viên.

    Heuristic:
    - Duyệt 10 dòng đầu tiên của CV.
    - Bỏ qua dòng chứa email.
    - Chọn dòng có 2–5 từ toàn chữ cái.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    header_lines = lines[:10]

    for line in header_lines:
        if "@" in line:
            continue

        tokens = [w for w in line.split() if w.isalpha()]
        if 2 <= len(tokens) <= 5:
            return line.strip()

    return None


def _extract_skills(text: str) -> List[str]:
    """Tìm kỹ năng bằng keyword search (1 từ hoặc nhiều từ)."""
    text_lower = text.lower()
    tokens = set(word_tokenize(text_lower))

    found = set()

    for skill in SKILL_KEYWORDS:
        if " " in skill:
            # multi-word skill (vd: machine learning)
            if skill in text_lower:
                found.add(skill)
        else:
            # single-word skill
            if skill in tokens:
                found.add(skill)

    return [s.title() for s in sorted(found)]


def extract_entities(text: str) -> Dict:
    """
    Hàm chính của Module 2.

    Nhận raw text → trích xuất thực thể → trả về dictionary.
    """
    email = _extract_email(text)
    phone = _extract_phone(text)
    name = _extract_name(text)
    skills = _extract_skills(text)

    entities = ExtractedEntities(
        name=name,
        email=email,
        phone=phone,
        skills=skills
    )

    return entities.to_dict()


if __name__ == "__main__":
    # Test nhanh Module 2
    sample_text = """
    NGUYEN VAN A
    Email: nguyenvana@example.com
    Phone: +84 912 999 888
    Skills: Python, SQL, Machine Learning, Docker
    """

    print(extract_entities(sample_text))
