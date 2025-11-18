from app import db
from app.models import Job, Candidate, CV_File


# QUAN LY JOB
def create_job(title, description, requirements):
    """Tao Job va luu vao CSDL"""
    new_job = Job(title=title, description=description, requirements=requirements)
    db.session.add(new_job)
    db.session.commit()
    return new_job


def get_all_jobs():
    """Lấy tất cả các Job từ CSDL"""
    return Job.query.order_by(
        Job.created_at.desc()
    ).all()  # lay tat ca job sap xep theo thoi giann


def get_job_by_id(job_id):
    """Lấy một Job theo ID"""
    return Job.query.get(job_id)


# PHAN 2 QUAN LY UNG VIEN
def create_candidate(name, email, phone):
    """Tao Candidate va luu vao CSDL"""
    new_candidate = Candidate(name=name, email=email, phone=phone)
    db.session.add(new_candidate)
    db.session.commit()
    return new_candidate


def get_all_candidates():
    """Lấy tất cả các Candidate từ CSDL"""
    return Candidate.query.order_by(Candidate.created_at.desc()).all()


def get_candidate_by_id(candidate_id):
    """Lấy một Candidate theo ID"""
    return Candidate.query.get(candidate_id)


# Quan ly CV File
def save_cv_file(candidate_id, file_path, raw_text=""):
    """
    Luu thong tin file CV da boc tach.
    """
    new_cv = CV_File(candidate_id=candidate_id, file_path=file_path, raw_text=raw_text)
    db.session.add(new_cv)
    db.session.commit()
    return new_cv
