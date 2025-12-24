# app/models/market.py
from app import db
from datetime import datetime


class MarketData(db.Model):
    """
    Bảng lưu trữ dữ liệu thị trường tổng hợp (Market Intelligence).
    """

    __tablename__ = "market_data"

    id = db.Column(db.Integer, primary_key=True)

    # Chuẩn hóa tên việc làm (VD: "Backend Developer", "Marketing Executive")
    job_title_normalized = db.Column(db.String(200), nullable=False, index=True)

    # Level: FRESHER, JUNIOR, SENIOR, MANAGER...
    level = db.Column(db.String(50))

    # Mức lương trung bình thị trường (Triệu VNĐ)
    avg_salary_min = db.Column(db.Float)
    avg_salary_max = db.Column(db.Float)
    currency = db.Column(db.String(10), default="VND")

    # Điểm nhu cầu (1-100), càng cao càng hot
    demand_score = db.Column(db.Integer)

    # List skill phổ biến (Lưu JSON). VD: ["Python", "AWS", "English"]
    top_skills = db.Column(db.JSON)

    # Thời điểm cập nhật dữ liệu
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MarketData {self.job_title_normalized} - {self.level}>"
