from app.extensions import db
from datetime import datetime


class Job(db.Model):
    __tablename__ = "jobs"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200))

    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    recruiter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    salary_min = db.Column(db.Float)
    salary_max = db.Column(db.Float)
    currency = db.Column(db.String(10), default="VND")
    location = db.Column(db.String(100))
    level = db.Column(db.String(50))

    description = db.Column(db.Text)
    requirements = db.Column(db.Text)
    benefits = db.Column(db.Text)

    source = db.Column(db.String(50), default="INTERNAL")
    original_url = db.Column(db.Text)

    skills_required = db.Column(db.JSON)
    min_years_experience = db.Column(db.Integer, default=0)
    mini_test_config = db.Column(db.JSON)
    structured_config = db.Column(db.JSON, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    vector_embedding = db.Column(db.PickleType, nullable=True)
