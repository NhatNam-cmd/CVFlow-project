# services/ai_engine/parser.py
import pdfplumber


def extract_text_from_pdf(pdf_path):
    """
    Đọc toàn bộ text từ file PDF.
    """
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Lỗi đọc PDF: {e}")
        return None

    return text.strip()
