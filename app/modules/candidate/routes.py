import os
import time
from datetime import datetime
from flask import render_template, redirect, url_for, flash, current_app, request
from flask_login import current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.modules.candidate import candidate_bp

# Import forms
from app.modules.candidate.forms import CandidateProfileForm, CVUploadForm
from app.models.application import CV_File, Application
from app.models.scheduler import Interview


@candidate_bp.before_request
def check_candidate_role():
    if not current_user.is_authenticated or current_user.role != "CANDIDATE":
        flash("Trang này chỉ dành cho Ứng viên.", "warning")
        return redirect(url_for("auth.login"))


@candidate_bp.route("/dashboard")
def dashboard():
    applied_count = Application.query.filter_by(user_id=current_user.id).count()
    interested_count = Application.query.filter(
        Application.user_id == current_user.id, Application.status != "NEW"
    ).count()

    # Lấy lịch phỏng vấn sắp tới
    upcoming_interviews = (
        Interview.query.join(Application)
        .filter(
            Application.user_id == current_user.id,
            Interview.start_time > datetime.utcnow(),
        )
        .order_by(Interview.start_time.asc())
        .all()
    )

    recent_activities = (
        Application.query.filter_by(user_id=current_user.id)
        .order_by(Application.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "candidate/dashboard.html",
        applied_count=applied_count,
        interested_count=interested_count,
        interview_count=len(upcoming_interviews),
        upcoming_interviews=upcoming_interviews,
        recent_activities=recent_activities,
    )


@candidate_bp.route("/profile", methods=["GET", "POST"])
def profile():
    form = CandidateProfileForm()

    if request.method == "GET":
        # 1. Load dữ liệu cơ bản
        form.phone.data = current_user.phone if current_user.phone else ""
        form.bio.data = current_user.bio if current_user.bio else ""

        # 2. Load dữ liệu Lịch rảnh (Availability)
        # Database lưu chuỗi "Mon,Tue" -> Form cần list ['Mon', 'Tue']
        if current_user.available_days:
            form.available_days.data = current_user.available_days.split(",")

        # Load giờ rảnh (Python Time object -> Form Field tự hiểu)
        form.start_time.data = current_user.start_time
        form.end_time.data = current_user.end_time

    if form.validate_on_submit():
        # Cập nhật thông tin cơ bản
        current_user.phone = form.phone.data
        current_user.bio = form.bio.data

        # Cập nhật Lịch rảnh
        # Form trả về List ['Mon', 'Tue'] -> Database cần lưu chuỗi "Mon,Tue"
        if form.available_days.data:
            current_user.available_days = ",".join(form.available_days.data)
        else:
            current_user.available_days = ""  # Xử lý trường hợp bỏ chọn hết

        current_user.start_time = form.start_time.data
        current_user.end_time = form.end_time.data

        try:
            db.session.commit()
            flash("Cập nhật hồ sơ thành công!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi khi lưu dữ liệu: {str(e)}", "danger")

        return redirect(url_for("candidate.profile"))

    return render_template("candidate/profile.html", form=form)


@candidate_bp.route("/cv", methods=["GET", "POST"])
def cv_manager():
    form = CVUploadForm()

    if form.validate_on_submit():
        f = form.cv_file.data
        filename = secure_filename(f.filename)

        # Tạo tên file duy nhất để tránh trùng lặp
        timestamp = int(time.time())
        unique_filename = f"{current_user.id}_{timestamp}_{filename}"

        if not os.path.exists(current_app.config["UPLOAD_FOLDER"]):
            os.makedirs(current_app.config["UPLOAD_FOLDER"])

        file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)

        try:
            f.save(file_path)

            # Tắt cờ CV chính của các file cũ nếu cần (tùy logic, ở đây mình cứ lưu bình thường)
            # Nếu muốn file mới auto là chính thì thêm logic update ở đây.

            new_cv = CV_File(
                user_id=current_user.id,
                file_url=unique_filename,
                file_name=filename,
                is_main=False,  # Mặc định CV mới chưa là chính
            )
            db.session.add(new_cv)
            db.session.commit()
            flash("Tải CV lên thành công!", "success")
        except Exception as e:
            flash(f"Lỗi khi lưu file: {str(e)}", "danger")

        return redirect(url_for("candidate.cv_manager"))

    cvs = (
        CV_File.query.filter_by(user_id=current_user.id)
        .order_by(CV_File.created_at.desc())
        .all()
    )
    return render_template("candidate/cv_manager.html", form=form, cvs=cvs)


@candidate_bp.route("/cv/set-main/<int:cv_id>")
def set_main_cv(cv_id):
    # Reset tất cả về False
    CV_File.query.filter_by(user_id=current_user.id).update({"is_main": False})

    # Set file được chọn thành True
    target_cv = CV_File.query.filter_by(id=cv_id, user_id=current_user.id).first()
    if target_cv:
        target_cv.is_main = True
        db.session.commit()
        flash("Đã đặt làm CV chính.", "success")
    else:
        flash("Không tìm thấy CV.", "danger")

    return redirect(url_for("candidate.cv_manager"))


@candidate_bp.route("/jobs")
def job_manager():
    applications = Application.query.filter_by(user_id=current_user.id).all()
    return render_template("candidate/job_manager.html", applications=applications)


@candidate_bp.route("/interviews")
def interview_list():
    interviews = (
        Interview.query.join(Application)
        .filter(Application.user_id == current_user.id)
        .order_by(Interview.start_time.desc())
        .all()
    )
    return render_template("candidate/interview_list.html", interviews=interviews)
