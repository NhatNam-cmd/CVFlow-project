from app import db
from app.models import Job, Candidate, CV_File
from app.models import Score
from typing import List, Optional, Any  # Thêm Type Hints cho chuyên nghiệp

# --- QUẢN LÝ JOB ---


def create_job(title: str, description: str, requirements: str) -> Optional[Job]:
    """
    Tạo Job và lưu vào CSDL.
    Trả về object Job nếu thành công, None nếu lỗi.
    """
    try:
        new_job = Job(title=title, description=description, requirements=requirements)
        db.session.add(new_job)
        db.session.commit()
        return new_job
    except Exception as e:
        db.session.rollback()  # Quan trọng: Hoàn tác nếu lỗi để tránh kẹt DB
        print(f"Error creating job: {e}")  # Log đơn giản ra console
        return None


def get_all_jobs() -> List[Job]:
    """Lấy tất cả các Job, sắp xếp mới nhất trước."""
    # Sử dụng cách query hiện đại của SQLAlchemy 2.0 style
    # (tùy chọn, giữ cách cũ cũng được nếu quen)
    # Ở đây giữ cách cũ cho đơn giản và quen thuộc với nhóm
    return Job.query.order_by(Job.created_at.desc()).all()


def get_job_by_id(job_id: int) -> Optional[Job]:
    """Lấy một Job theo ID."""
    return db.session.get(Job, job_id)  # Sửa lỗi Deprecated của query.get


# --- QUẢN LÝ ỨNG VIÊN (CANDIDATE) ---


def create_candidate(name: str, email: str, phone: str) -> Optional[Candidate]:
    """Tạo Candidate mới."""
    try:
        new_candidate = Candidate(name=name, email=email, phone=phone)
        db.session.add(new_candidate)
        db.session.commit()
        return new_candidate
    except Exception as e:
        db.session.rollback()
        print(f"Error creating candidate: {e}")
        return None


def get_all_candidates() -> List[Candidate]:
    """Lấy tất cả ứng viên."""
    return Candidate.query.order_by(Candidate.created_at.desc()).all()


def get_candidate_by_id(candidate_id: int) -> Optional[Candidate]:
    """Lấy một Candidate theo ID."""
    return db.session.get(Candidate, candidate_id)


# --- QUẢN LÝ FILE CV ---


def save_cv_file(
    candidate_id: int, file_path: str, raw_text: str = ""
) -> Optional[CV_File]:
    """
    Lưu thông tin file CV.
    Lưu ý: raw_text là kết quả từ Module 1 (Xử lý File).
    """
    try:
        new_cv = CV_File(
            candidate_id=candidate_id, file_path=file_path, raw_text=raw_text
        )
        db.session.add(new_cv)
        db.session.commit()
        return new_cv
    except Exception as e:
        db.session.rollback()
        print(f"Error saving CV file: {e}")
        return None


def create_init_score(candidate_id: int, job_id: int):
    """
    Tạo bản ghi liên kết Candidate và Job trong bảng Score.
    Khởi tạo điểm số là None (hoặc 0) để chờ Pipeline xử lý sau.
    """
    try:
        # Kiểm tra xem đã nộp chưa để tránh duplicate (tùy chọn)
        existing_score = Score.query.filter_by(
            candidate_id=candidate_id, job_id=job_id
        ).first()
        if existing_score:
            return existing_score

        new_score = Score(
            candidate_id=candidate_id,
            job_id=job_id,
            score_value=0.0,  # Giá trị mặc định
            match_value=0.0,
        )
        db.session.add(new_score)
        db.session.commit()
        return new_score
    except Exception as e:
        db.session.rollback()
        print(f"Error linking candidate to job: {e}")
        return None


# (+) THÊM MỚI: Hàm cập nhật thông tin sau khi AI chạy xong
def update_cv_data(
    cv_id: int, summary: str, structured_data: dict, vector: Any
) -> bool:
    """Cập nhật CV với dữ liệu từ AI (Tóm tắt, JSON, Vector)"""
    try:
        cv = db.session.get(CV_File, cv_id)
        if cv:
            cv.summary_text = summary
            cv.structured_data = structured_data  # Lưu JSON
            cv.vector_embedding = vector  # Lưu Vector
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Error updating CV data: {e}")
        return False


def update_job_vector(job_id: int, vector: Any) -> bool:
    """Cập nhật Vector cho Job (để so khớp sau này)"""
    try:
        job = db.session.get(Job, job_id)
        if job:
            job.vector_embedding = vector
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Error updating Job vector: {e}")
        return False
