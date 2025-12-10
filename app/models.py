from app import db
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import (
    JSONB,
)  # Dùng cho Postgres

# ==========================================
# 1. NHÓM NGƯỜI DÙNG & CÔNG TY
# ==========================================


class Company(db.Model):
    __tablename__ = "companies"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True)
    logo_url = db.Column(db.String(500))
    website = db.Column(db.String(200))
    address = db.Column(db.Text)
    description = db.Column(db.Text)

    # Feature 2: Market Intelligence
    industry = db.Column(db.String(100))  # Fintech, Outsourcing...

    # Enterprise: Xác thực
    tax_number = db.Column(db.String(50), unique=True)
    verification_status = db.Column(
        db.String(20), default="PENDING"
    )  # PENDING, VERIFIED

    # Quan hệ
    recruiters = db.relationship("User", backref="company", lazy=True)
    jobs = db.relationship("Job", backref="company", lazy=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # ADMIN, HR, CANDIDATE
    avatar_url = db.Column(db.String(500))

    # Dành cho Candidate
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    is_open_to_work = db.Column(db.Boolean, default=True)

    # Dành cho HR
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Quan hệ
    cvs = db.relationship("CV_File", backref="candidate", lazy=True)
    availabilities = db.relationship("Availability", backref="user", lazy=True)


# ==========================================
# 2. NHÓM VIỆC LÀM (JOB)
# ==========================================


class Job(db.Model):
    __tablename__ = "jobs"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200))

    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    recruiter_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )  # Null nếu là job cào

    # Feature 2: Market Intelligence
    salary_min = db.Column(db.Float)
    salary_max = db.Column(db.Float)
    currency = db.Column(db.String(10), default="VND")
    location = db.Column(db.String(100))  # Hanoi, HCM...
    level = db.Column(db.String(50))  # Junior, Senior...

    description = db.Column(db.Text)
    requirements = db.Column(db.Text)
    benefits = db.Column(db.Text)

    # Feature 4: Crawler
    source = db.Column(db.String(50), default="INTERNAL")  # INTERNAL, TOPDEV...
    original_url = db.Column(db.Text)

    # Feature 1: Automation Config
    # Lưu JSON: ["Python", "SQL"]
    # Lưu ý: Nếu dùng SQLite thì đổi JSONB thành Text và xử lý bằng json.loads
    skills_required = db.Column(JSONB)
    min_years_exp = db.Column(db.Integer, default=0)
    # Lưu JSON: {"question": "...", "options": [], "correct": "A"}
    mini_test_config = db.Column(JSONB)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Vector Embedding cho Job Matching
    vector_embedding = db.Column(db.PickleType)


# ==========================================
# 3. NHÓM ỨNG TUYỂN & CV
# ==========================================


class CV_File(db.Model):
    __tablename__ = "cv_files"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    file_url = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(200))
    is_main = db.Column(db.Boolean, default=False)

    # AI Analysis
    raw_text = db.Column(db.Text)
    ai_score = db.Column(db.Integer)
    # Lưu JSON kết quả phân tích AI
    ai_matching_data = db.Column(JSONB)
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

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Quan hệ
    job = db.relationship("Job", backref="applications")
    candidate = db.relationship("User", foreign_keys=[user_id], backref="applications")
    cv = db.relationship("CV_File")


# ==========================================
# 4. NHÓM LỊCH PHỎNG VẤN (SCHEDULER)
# ==========================================


class Availability(db.Model):
    __tablename__ = "availabilities"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # 0=CN, 1=T2... 6=T7
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

    # File ICS sinh ra bởi Python
    ics_file_url = db.Column(db.String(500))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Quan hệ
    application = db.relationship("Application", backref="interviews")
