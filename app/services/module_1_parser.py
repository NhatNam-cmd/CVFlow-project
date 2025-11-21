"""
module_1_parser.py

Module 1 - Xử lý và trích xuất văn bản thô từ file CV (.pdf, .docx).

Yêu cầu từ CVFlow:
- Nhận đường dẫn file (path) của CV.
- Trả về một chuỗi (string) chứa 100% văn bản thô (raw text).
- Hỗ trợ .pdf (PyPDF2) và .docx (python-docx).
"""

from pathlib import Path
from typing import Union

import PyPDF2
import docx


def _extract_text_from_pdf(file_path: Union[str, Path]) -> str:
    """
    Đọc toàn bộ text từ file PDF.

    :param file_path: Đường dẫn tới file PDF.
    :return: Chuỗi văn bản thô.
    """
    path = Path(file_path)
    text_parts: list[str] = []

    with path.open("rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)

    return "\n".join(text_parts).strip()


def _extract_text_from_docx(file_path: Union[str, Path]) -> str:
    """
    Đọc toàn bộ text từ file DOCX.

    :param file_path: Đường dẫn tới file DOCX.
    :return: Chuỗi văn bản thô.
    """
    path = Path(file_path)
    document = docx.Document(str(path))
    paragraphs = [p.text for p in document.paragraphs if p.text]
    return "\n".join(paragraphs).strip()


def extract_text_from_file(file_path: Union[str, Path]) -> str:
    """
    Hàm chính của Module 1.

    Nhận đường dẫn file (.pdf hoặc .docx) và trả về văn bản thô.
    Nếu phần mở rộng không hỗ trợ -> raise ValueError.

    :param file_path: Đường dẫn tới file CV.
    :return: Văn bản thô (raw text).
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File không tồn tại: {path}")

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_text_from_pdf(path)
    if suffix == ".docx":
        return _extract_text_from_docx(path)

    raise ValueError(f"Định dạng file không được hỗ trợ: {suffix}")


if __name__ == "__main__":
    # Đoạn test nhỏ (chạy tay) – có thể xóa khi viết unit test chính thức.
    sample_path = "sample_cv.pdf"  # đổi lại đường dẫn để test
    try:
        raw = extract_text_from_file(sample_path)
        print("=== RAW TEXT PREVIEW (500 chars) ===")
        print(raw[:500])
    except Exception as exc:
        print(f"Lỗi: {exc}")
