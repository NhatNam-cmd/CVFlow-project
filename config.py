import os

# Lấy đường dẫn tuyệt đối của thư mục chứa file config.py
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Cấu hình cơ sở cho ứng dụng."""

    # Khóa bí mật để bảo vệ form và session
    SECRET_KEY = os.environ.get("SECRET_KEY") or "cvflow-super-secret-key"

    # Cấu hình CSDL SQLite
    # Đảm bảo CSDL nằm trong thư mục data/
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URI"
    ) or "sqlite:///" + os.path.join(basedir, "data", "cvflow.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mật khẩu Admin (hard-coded cho MVP theo kế hoạch)
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or "cvflow_admin_123"

    # Đường dẫn thư mục UPLOADS
    UPLOAD_FOLDER = os.path.join(basedir, "data", "uploads")
    ALLOWED_EXTENSIONS = {"pdf", "docx"}
