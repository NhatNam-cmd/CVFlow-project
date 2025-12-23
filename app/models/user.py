from app.extensions import db, bcrypt
from flask_login import UserMixin
from datetime import datetime


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="CANDIDATE")
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(255))
    # Quan hệ
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    available_days = db.Column(db.String(50), nullable=True)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)

    # 1. Getter password (không cho đọc)
    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    # 2. Setter password (tự động mã hóa khi gán user.password = '...')
    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    # 3. Hàm kiểm tra mật khẩu (Sửa lỗi AttributeError check_password)
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class Company(db.Model):
    __tablename__ = "companies"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True)
    logo_url = db.Column(db.String(255))
    website = db.Column(db.String(255))
    address = db.Column(db.String(255))
    description = db.Column(db.Text)
    industry = db.Column(db.String(100))

    # Thông tin pháp lý
    tax_number = db.Column(db.String(20), unique=True)
    verification_status = db.Column(
        db.String(20), default="PENDING"
    )  # PENDING, VERIFIED, REJECTED

    # Quan hệ
    employees = db.relationship("User", backref="company", lazy=True)
    jobs = db.relationship("Job", backref="company", lazy=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
