from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON


class CV_File(db.Model):
    __tablename__ = "cv_files"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    file_url = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(200))
    is_main = db.Column(db.Boolean, default=False)

    # AI Analysis
    raw_text = db.Column(db.Text)
    ai_score = db.Column(db.Integer, default=0)
    ai_matching_data = db.Column(db.JSON)
    vector_embedding = db.Column(db.PickleType)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Application(db.Model):
    __tablename__ = "applications"
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    cv_id = db.Column(db.Integer, db.ForeignKey("cv_files.id"), nullable=True)

    cover_letter = db.Column(db.Text)

    # Kanban Status: NEW, SCREENED, INTERVIEW, OFFER, REJECTED
    status = db.Column(db.String(50), default="NEW")
    # Feature 2: Analytics (Tại sao trượt?)
    rejected_reason = db.Column(db.String(200))

    # Feature 1: Mini-Test Result
    mini_test_answer = db.Column(db.String(10))
    mini_test_score = db.Column(db.Integer)

    # AI Score riêng cho Job này
    match_score = db.Column(db.Integer)
    ai_analysis = db.Column(JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Quan hệ
    job = db.relationship("Job", backref="applications")
    candidate = db.relationship("User", foreign_keys=[user_id], backref="applications")
    cv = db.relationship("CV_File")
