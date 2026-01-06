from flask import render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import current_user, login_required
from app.extensions import db
from app.modules.hr import hr_bp
from app.modules.hr.forms import CompanyProfileForm, JobPostForm
from app.models.job import Job
from app.models.user import Company
from app.models.application import Application
from app.models.scheduler import Interview
from datetime import datetime
from datetime import timedelta
from app.services.ai_engine.cv_analyzer import CVAnalyzer
from sqlalchemy import func
from app.services.ai_engine.gemini_client import get_text_embedding


# Middleware kiểm tra quyền HR
@hr_bp.before_request
def check_hr_role():
    if not current_user.is_authenticated or current_user.role != "HR":
        flash("Bạn không có quyền truy cập trang này.", "danger")
        return redirect(url_for("auth.login"))


@hr_bp.route("/dashboard")
@login_required
def dashboard():
    # Kiểm tra nếu HR chưa có công ty (tránh lỗi)
    if not current_user.company_id:
        return render_template("hr/dashboard.html", error="Chưa liên kết công ty")

    company_id = current_user.company_id

    # 1. TỔNG SỐ CV NHẬN ĐƯỢC (Chỉ tính cho các Job thuộc công ty này)
    # Join bảng Application với Job, lọc theo company_id của Job
    total_cvs = Application.query.join(Job).filter(Job.company_id == company_id).count()

    # 2. LỊCH PHỎNG VẤN SẮP TỚI (Của công ty này)
    # Join Interview -> Application -> Job -> Lọc company_id
    upcoming_interviews = (
        Interview.query.join(Application)
        .join(Job)
        .filter(
            Job.company_id == company_id,
            Interview.start_time > datetime.utcnow(),
            Interview.status == "SCHEDULED",
        )
        .count()
    )

    # 3. TIN ĐANG MỞ (SỬA LỖI CỦA BẠN TẠI ĐÂY)
    # Thêm điều kiện company_id == company_id
    active_jobs_count = Job.query.filter(
        Job.is_active == True, Job.company_id == company_id
    ).count()

    # 4. ĐIỂM AI TRUNG BÌNH (Chỉ tính hồ sơ nộp vào công ty này)
    avg_query = (
        db.session.query(func.avg(Application.match_score))
        .join(Job)
        .filter(Job.company_id == company_id, Application.match_score > 0)
        .scalar()
    )

    avg_ai_score = int(avg_query) if avg_query else 0

    # 5. DANH SÁCH ỨNG VIÊN MỚI NHẤT (Của công ty này)
    recent_applications = (
        Application.query.join(Job)
        .filter(Job.company_id == company_id)
        .order_by(Application.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "hr/dashboard.html",
        total_cvs=total_cvs,
        upcoming_interviews=upcoming_interviews,
        active_jobs_count=active_jobs_count,
        recent_applications=recent_applications,
        avg_ai_score=avg_ai_score,
    )


@hr_bp.route("/company", methods=["GET", "POST"])
def company_profile():
    company = db.session.get(Company, current_user.company_id)
    form = CompanyProfileForm(obj=company)  # Auto fill dữ liệu cũ

    if form.validate_on_submit():
        form.populate_obj(company)  # Update ngược lại object
        db.session.commit()
        flash("Cập nhật hồ sơ công ty thành công!", "success")
        return redirect(url_for("hr.company_profile"))

    return render_template("hr/company_profile.html", form=form, company=company)


@hr_bp.route("/post-job", methods=["GET", "POST"])
def post_job():
    form = JobPostForm()
    if form.validate_on_submit():
        # Xử lý skill tags
        skills_list = [s.strip() for s in form.skills_required.data.split(",")]

        # --- XỬ LÝ MINI-TEST (MỚI) ---
        mini_test_json = None
        # Chỉ lưu nếu người dùng có nhập câu hỏi
        if form.test_question.data:
            mini_test_json = {
                "question": form.test_question.data,
                "options": [
                    {"id": "A", "text": form.option1.data},
                    {"id": "B", "text": form.option2.data},
                    {"id": "C", "text": form.option3.data},
                    {"id": "D", "text": form.option4.data},
                ],
                "correct": form.correct_answer.data,
            }

        job = Job(
            title=form.title.data,
            company_id=current_user.company_id,
            recruiter_id=current_user.id,
            salary_min=form.salary_min.data,
            salary_max=form.salary_max.data,
            location=form.location.data,
            level=form.level.data,
            description=form.description.data,
            requirements=form.requirements.data,
            benefits=form.benefits.data,
            skills_required=skills_list,
            # Lưu cấu hình test vào DB
            mini_test_config=mini_test_json,
            created_at=datetime.utcnow(),
        )
        full_text = f"{job.title} . {job.description} . {job.requirements}"
        job.vector_embedding = get_text_embedding(full_text)
        db.session.add(job)
        db.session.commit()
        flash("Đăng tin tuyển dụng thành công!", "success")
        return redirect(url_for("hr.my_jobs"))

    return render_template("hr/post_job.html", form=form)


@hr_bp.route("/my-jobs")
def my_jobs():
    jobs = (
        Job.query.filter_by(company_id=current_user.company_id)
        .order_by(Job.created_at.desc())
        .all()
    )
    return render_template("hr/my_jobs.html", jobs=jobs)


@hr_bp.route("/candidates")
def candidate_list():
    # Lọc theo Job nếu có param ?job_id=...
    job_id = request.args.get("job_id", type=int)

    query = Application.query.join(Job).filter(
        Job.company_id == current_user.company_id
    )

    if job_id:
        query = query.filter(Application.job_id == job_id)
        current_job_name = Job.query.get(job_id).title
    else:
        current_job_name = "Tất cả vị trí"

    applications = query.all()

    # Lấy danh sách jobs để đổ vào dropdown filter
    all_jobs = Job.query.filter_by(company_id=current_user.company_id).all()

    # Phân loại Kanban
    kanban_data = {
        "NEW": [app for app in applications if app.status == "NEW"],
        "INTERVIEW": [app for app in applications if app.status == "INTERVIEW"],
        "OFFER": [app for app in applications if app.status == "OFFER"],
        "REJECTED": [app for app in applications if app.status == "REJECTED"],
    }

    return render_template(
        "hr/candidate_list.html",
        kanban=kanban_data,
        all_jobs=all_jobs,
        current_job_id=job_id,
        current_job_name=current_job_name,
    )


@hr_bp.route("/candidate/<int:id>")
def candidate_view(id):
    application = db.session.get(Application, id)
    if not application or application.job.company_id != current_user.company_id:
        abort(403)  # Không được xem ứng viên của cty khác

    return render_template("hr/candidate_view.html", application=application)


@hr_bp.route("/schedule")
def schedule_calendar():
    # 1. Lấy tất cả lịch phỏng vấn của HR đang đăng nhập
    interviews = Interview.query.filter_by(recruiter_id=current_user.id).all()

    # 2. Chuyển đổi sang định dạng List of Dictionaries cho FullCalendar
    events = []
    for i in interviews:
        # Quy định màu sắc: Sắp tới (Vàng), Đã xong (Xanh), Hủy (Đỏ)
        color = "#ffc107"  # Warning (Yellow)
        if i.status == "COMPLETED":
            color = "#198754"  # Success (Green)
        elif i.status == "CANCELLED":
            color = "#dc3545"  # Danger (Red)

        events.append(
            {
                "title": f"PV: {i.application.candidate.full_name} ({i.application.job.title})",
                "start": i.start_time.isoformat(),  # Format: 2025-12-12T09:00:00
                "end": i.end_time.isoformat(),
                "url": url_for(
                    "hr.candidate_view", id=i.application.id
                ),  # Bấm vào lịch thì nhảy sang xem chi tiết
                "backgroundColor": color,
                "borderColor": color,
                "textColor": "#000" if i.status == "SCHEDULED" else "#fff",
            }
        )

    return render_template("hr/schedule_calendar.html", events=events)


@hr_bp.route("/profile")
def profile():
    return render_template("hr/profile.html")


@hr_bp.route("/candidate/status/<int:id>/<string:new_status>")
def update_status(id, new_status):
    """
    API đổi trạng thái ứng viên (Chuyển cột Kanban)
    """
    # 1. Lấy hồ sơ
    application = db.session.get(Application, id)

    # 2. Bảo mật: Kiểm tra xem hồ sơ này có thuộc cty của HR đang login không
    if not application or application.job.company_id != current_user.company_id:
        flash("Lỗi: Không tìm thấy hồ sơ hoặc không có quyền truy cập.", "danger")
        return redirect(url_for("hr.candidate_list"))

    # 3. Kiểm tra trạng thái hợp lệ
    valid_statuses = ["NEW", "INTERVIEW", "OFFER", "REJECTED"]
    if new_status not in valid_statuses:
        flash("Trạng thái không hợp lệ.", "warning")
        return redirect(request.referrer)

    # 4. Cập nhật & Lưu
    application.status = new_status
    db.session.commit()

    flash(f"Đã chuyển trạng thái ứng viên sang: {new_status}", "success")

    # Quay lại trang trước đó (Kanban hoặc Detail)
    return redirect(request.referrer)


@hr_bp.route("/interview/create/<int:app_id>", methods=["POST"])
def create_interview(app_id):
    # 1. Lấy dữ liệu
    application = db.session.get(Application, app_id)
    if not application or application.job.company_id != current_user.company_id:
        abort(403)

    start_time_str = request.form.get("start_time")
    duration = int(request.form.get("duration", 60))
    location_detail = request.form.get("location_detail")

    # 2. Tính toán thời gian
    start_time = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M")
    end_time = start_time + timedelta(minutes=duration)

    # 3. Tạo record Interview
    interview = Interview(
        application_id=application.id,
        recruiter_id=current_user.id,
        start_time=start_time,
        end_time=end_time,
        location=location_detail,
        meeting_link=location_detail if "http" in location_detail else None,
        status="SCHEDULED",
        created_at=datetime.utcnow(),
    )

    db.session.add(interview)
    db.session.commit()

    flash("Đã lên lịch phỏng vấn thành công!", "success")
    return redirect(url_for("hr.candidate_view", id=app_id))


# File: app/modules/hr/routes.py


@hr_bp.route("/applications/<int:app_id>/reject", methods=["POST"])
@login_required  # 1. BẮT BUỘC: Phải đăng nhập mới được dùng
def reject_application(app_id):
    # 2. Tìm ứng viên (Dùng get_or_404 cho gọn, nếu không thấy tự trả về 404)
    application = Application.query.get_or_404(app_id)

    # 3. Lấy dữ liệu gửi lên
    data = request.get_json()

    # Validation: Kiểm tra dữ liệu đầu vào
    if not data or "reason" not in data:
        return (
            jsonify({"success": False, "message": "Vui lòng chọn lý do từ chối!"}),
            400,
        )

    reason = data["reason"]

    try:
        # 4. Xử lý logic
        application.status = "REJECTED"
        application.rejected_reason = reason

        # Lưu vào DB
        db.session.commit()

        return jsonify({"success": True, "message": "Đã từ chối ứng viên thành công."})

    except Exception as e:
        # 5. Xử lý lỗi hệ thống (Database sập, lỗi mạng...)
        db.session.rollback()
        print(f"ERROR [Reject App]: {str(e)}")  # Chỉ in 1 dòng lỗi gọn gàng
        return (
            jsonify(
                {"success": False, "message": "Lỗi hệ thống, vui lòng thử lại sau."}
            ),
            500,
        )


@hr_bp.route("/analyze-cv/<int:app_id>", methods=["POST"])
@login_required
def analyze_application_cv(app_id):  # <-- Đổi tên hàm thành analyze_application_cv
    """
    Route xử lý khi HR bấm nút 'Phân tích lại'
    """
    try:
        analyzer = CVAnalyzer()

        # Gọi Service để chấm điểm (force_refresh=True để ép chấm lại)
        analyzer.analyze_application(app_id, force_refresh=True)

        flash("Đã phân tích xong!", "success")
    except Exception as e:
        flash(f"Lỗi khi phân tích: {str(e)}", "danger")
        print(f"Error HR Analyze: {e}")

    return redirect(request.referrer)
