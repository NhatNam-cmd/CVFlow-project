import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-key-nhung-khong-nen-dung"

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError(
            "❌ LỖI NGHIÊM TRỌNG: Chưa cấu hình DATABASE_URL trong file .env! Hệ thống bắt buộc dùng PostgreSQL."
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Giới hạn file 16MB
    ALLOWED_EXTENSIONS = {"pdf", "docx"}

    CELERY_BROKER_URL = os.environ.get("REDIS_URL") or "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL") or "redis://localhost:6379/0"

    MAIL_SERVER = os.environ.get("MAIL_SERVER") or "smtp.gmail.com"
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 587)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS") == "True"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")


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
    DEBUG = False

    def __init__(self):
        super().__init__()

        self.SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URI")
        if not self.SQLALCHEMY_DATABASE_URI:
            raise ValueError(
                "FATAL ERROR: Biến môi trường 'DATABASE_URI' chưa được thiết lập cho Production!"
            )

        self.SECRET_KEY = os.environ.get("SECRET_KEY")
        if not self.SECRET_KEY or self.SECRET_KEY == "cvflow-fallback-secret-key-2025":
            raise ValueError(
                "FATAL ERROR: Biến môi trường 'SECRET_KEY' chưa được thiết lập hoặc không an toàn!"
            )


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
