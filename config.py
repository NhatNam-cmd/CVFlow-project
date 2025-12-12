import os
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

# Đường dẫn gốc của dự án
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Cấu hình cơ sở (Base Config) dùng chung cho mọi môi trường."""

    # 1. Bảo mật
    SECRET_KEY = os.environ.get("SECRET_KEY") or "cvflow-fallback-secret-key-2025"

    # 2. Database (Mặc định dùng SQLite nếu không có Postgres)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URI"
    ) or "sqlite:///" + os.path.join(BASE_DIR, "data", "cvflow.db")

    # 3. Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Giới hạn file 16MB
    ALLOWED_EXTENSIONS = {"pdf", "docx"}

    # 4. Redis & Celery (Cho Crawler & Background Task)
    CELERY_BROKER_URL = os.environ.get("REDIS_URL") or "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL") or "redis://localhost:6379/0"


class DevelopmentConfig(Config):
    """Cấu hình cho môi trường Dev (Code & Debug)."""

    DEBUG = True
    SQLALCHEMY_ECHO = False  # Đặt True nếu muốn xem câu lệnh SQL in ra console


class TestingConfig(Config):
    """Cấu hình cho môi trường Test (Chạy Unit Test)."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # Dùng RAM cho nhanh
    WTF_CSRF_ENABLED = False  # Tắt CSRF để test API dễ hơn


class ProductionConfig(Config):
    """Cấu hình cho môi trường Production (Chạy thật)."""

    DEBUG = False
    # Ở Prod, bắt buộc dùng biến môi trường mạnh
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URI")


# Dictionary để ánh xạ tên config
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
