from app import db  # Import db từ file __init__.py
from datetime import datetime


# Bảng 1: Job
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text, nullable=False)  # Lưu JSON dạng text
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Vector này giúp máy tính "hiểu" ý nghĩa của Job để so khớp
    vector_embedding = db.Column(db.PickleType, nullable=True)
    # Mối quan hệ: Một Job có nhiều Score
    scores = db.relationship("Score", backref="job", lazy="dynamic")


# Bảng 2: Candidate
class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    phone = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Mối quan hệ: Một Candidate có nhiều CV_File
    cv_files = db.relationship("CV_File", backref="candidate", lazy="dynamic")
    # Mối quan hệ: Một Candidate có nhiều Skill
    skills = db.relationship("Extracted_Skill", backref="candidate", lazy="dynamic")
    # Mối quan hệ: Một Candidate có nhiều Score
    scores = db.relationship("Score", backref="candidate", lazy="dynamic")


# Bảng 3: CV_File
class CV_File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(300), nullable=False)
    raw_text = db.Column(db.Text)
    summary_text = db.Column(db.Text)

    # (+) CỘT MỚI: Lưu toàn bộ thông tin AI trích xuất (JSON)
    # Ví dụ: {"years_exp": 3, "education": "Bachelor", "companies": ["FPT", "Viettel"]}
    # Giúp hiển thị chi tiết lên Admin Dashboard mà không cần tạo nhiều bảng con.
    structured_data = db.Column(db.JSON, nullable=True)

    # (+) CỘT MỚI: Lưu Vector của CV
    vector_embedding = db.Column(db.PickleType, nullable=True)

    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Khóa ngoại: Nối với Candidate
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidate.id"), nullable=False)


# Bảng 4: Extracted_Skill
class Extracted_Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    skill_name = db.Column(db.String(100), nullable=False)

    # Khóa ngoại: Nối với Candidate
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidate.id"), nullable=False)


# Bảng 5: Score
class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score_value = db.Column(db.Float)  # Điểm Module 4
    match_value = db.Column(db.Float)  # Điểm Module 5

    # (+) CỘT MỚI (Optional): Lý do chấm điểm của AI
    # Ví dụ: "Ứng viên này tốt nhưng thiếu kinh nghiệm Cloud"
    # Cái này cực kỳ giá trị để show cho HR xem.
    explanation = db.Column(db.Text, nullable=True)

    # Khóa ngoại: Nối với Candidate
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidate.id"), nullable=False)
    # Khóa ngoại: Nối với Job
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)

    # Đảm bảo 1 ứng viên chỉ có 1 điểm cho 1 job
    __table_args__ = (
        db.UniqueConstraint("candidate_id", "job_id", name="_candidate_job_uc"),
    )
