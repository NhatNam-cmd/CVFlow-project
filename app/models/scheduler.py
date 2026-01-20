from app.extensions import db
from datetime import datetime


class Availability(db.Model):
    __tablename__ = "availabilities"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    day_of_week = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)


class Interview(db.Model):
    __tablename__ = "interviews"
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(
        db.Integer, db.ForeignKey("applications.id"), nullable=False
    )
    recruiter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)

    location = db.Column(db.String(200))  # Online link hoặc phòng họp
    meeting_link = db.Column(db.String(500))
    status = db.Column(
        db.String(20), default="SCHEDULED"
    )  # SCHEDULED, COMPLETED, CANCELLED

    ics_file_url = db.Column(db.String(500))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    application = db.relationship("Application", backref="interviews")
