import time
from datetime import datetime
from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    current_app,
    request,
    jsonify,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app.extensions import db
from app.modules.candidate import candidate_bp
from app.services.ai_engine.core import review_cv_content
from app.services.ai_engine.parser import extract_text_from_pdf
import os
from app.services.ai_engine.gemini_client import get_text_embedding

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

    # 2. Lấy CV được chọn
    target_cv = CV_File.query.get_or_404(cv_id)
    target_cv.is_main = True

    # 3. TẠO VECTOR NẾU CHƯA CÓ (Lazy Loading)
    if not target_cv.vector_embedding and target_cv.raw_text:
        print("⚡ Đang tạo Vector Embedding cho CV...")
        target_cv.vector_embedding = get_text_embedding(target_cv.raw_text)

    db.session.commit()
    flash("Đã cập nhật CV chính & đồng bộ dữ liệu AI.", "success")
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


@candidate_bp.route("/cv-manager/review/<int:cv_id>", methods=["POST"])
@login_required
def ai_review_cv(cv_id):
    """
    API để Candidate yêu cầu AI chấm điểm CV của mình
    """
    # 1. Lấy CV từ DB (Đúng model CV_File)
    cv = CV_File.query.get_or_404(cv_id)

    # 2. Bảo mật: Chỉ chủ sở hữu mới được xem
    if cv.user_id != current_user.id:
        return (
            jsonify(
                {"success": False, "message": "Bạn không có quyền truy cập CV này"}
            ),
            403,
        )

    try:
        # 3. Kiểm tra xem đã có raw_text chưa (Tối ưu hóa)
        cv_text = cv.raw_text

        if not cv_text:
            # Nếu chưa có text, phải đọc từ file PDF
            file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], cv.file_url)

            if not os.path.exists(file_path):
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "File gốc không tồn tại trên server",
                        }
                    ),
                    404,
                )

            print(f"📄 Đang trích xuất text từ file: {cv.file_name}")
            cv_text = extract_text_from_pdf(file_path)

            # Lưu lại text vào DB để lần sau không phải đọc nữa
            if cv_text:
                cv.raw_text = cv_text
                db.session.commit()
            else:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "Không thể đọc nội dung text từ file PDF",
                        }
                    ),
                    400,
                )

        # 4. Gửi cho AI Review
        print(f"🤖 Đang gửi yêu cầu Review cho CV ID: {cv_id}")
        ai_result = review_cv_content(cv_text)

        if "error" in ai_result:
            return jsonify({"success": False, "message": ai_result["error"]}), 500

        # 5. Lưu kết quả vào DB
        cv.ai_score = ai_result.get("score", 0)
        cv.ai_matching_data = ai_result  # Tận dụng cột này để lưu kết quả Review

        db.session.commit()

        return jsonify(
            {"success": True, "message": "Đã phân tích xong!", "data": ai_result}
        )

    except Exception as e:
        print(f"❌ System Error: {e}")
        db.session.rollback()
        return jsonify({"success": False, "message": f"Lỗi hệ thống: {str(e)}"}), 500
