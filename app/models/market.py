from app import db
from datetime import datetime


class MarketData(db.Model):
    """
    Bảng lưu trữ dữ liệu thị trường tổng hợp (Market Intelligence).
    """

    __tablename__ = "market_data"

    id = db.Column(db.Integer, primary_key=True)

    job_title_normalized = db.Column(db.String(200), nullable=False, index=True)

    level = db.Column(db.String(50))

    avg_salary_min = db.Column(db.Float)
    avg_salary_max = db.Column(db.Float)
    currency = db.Column(db.String(10), default="VND")

    demand_score = db.Column(db.Integer)

    top_skills = db.Column(db.JSON)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MarketData {self.job_title_normalized} - {self.level}>"
