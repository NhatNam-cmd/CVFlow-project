import pdfplumber


def extract_text_from_pdf(file_path: str) -> str:
    """
    Đọc toàn bộ văn bản từ file PDF, cố gắng giữ layout.
    """
    full_text = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text.append(text)
        return "\n".join(full_text)
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return ""
