from app.extensions import db
from datetime import datetime


class MarketData(db.Model):
    __tablename__ = "market_data"
    id = db.Column(db.Integer, primary_key=True)
    job_title_normalized = db.Column(
        db.String(200), nullable=False, index=True
    )  # VD: "python developer"
    avg_salary_min = db.Column(db.Float)
    avg_salary_max = db.Column(db.Float)
    top_skills = db.Column(db.JSON)  # VD: ["Docker", "AWS", "RestAPI"]
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
