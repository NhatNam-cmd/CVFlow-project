from flask import render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import current_user, login_required
from app.extensions import db
from app.modules.hr import hr_bp
from app.modules.hr.forms import CompanyProfileForm, JobPostForm
from app.models.job import Job
from app.models.user import Company
from app.models.application import Application
from app.models.scheduler import Interview, Availability
from datetime import datetime, timedelta
from app.services.ai_engine.cv_analyzer import CVAnalyzer
from sqlalchemy import func
from app.services.ai_engine.gemini_client import get_text_embedding
from app.services.scheduler.engine import SchedulerEngine
from app.services.scheduler.ics_generator import ICSGenerator
# Import service gửi email mới thêm
from app.services.email_service import send_interview_invitation


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

    total_cvs = Application.query.join(Job).filter(Job.company_id == company_id).count()

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

    # 3. TIN ĐANG MỞ
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
        full_text_for_embedding = (
            f"{job.title} . {job.description} . {job.requirements}"
        )
        job.vector_embedding = get_text_embedding(full_text_for_embedding)
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
        abort(403)

    active_interview = Interview.query.filter_by(
        application_id=application.id, status="SCHEDULED"
    ).first()

    return render_template(
        "hr/candidate_view.html",
        application=application,
        active_interview=active_interview,
    )


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


@hr_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        # 1. Xử lý Tab Thông tin cá nhân
        if "full_name" in request.form:
            current_user.full_name = request.form.get("full_name")
            current_user.phone = request.form.get("phone")

            db.session.commit()
            flash("Cập nhật thông tin thành công!", "success")

        # 2. Xử lý Tab Cấu hình Lịch (Availability)
        # Form gửi lên dạng: day_0_active, day_0_start, day_0_end...
        if "save_availability" in request.form:
            try:

                Availability.query.filter_by(user_id=current_user.id).delete()

                for i in range(7):
                    is_active = request.form.get(f"day_{i}_active") == "on"
                    if is_active:
                        start_str = request.form.get(f"day_{i}_start")
                        end_str = request.form.get(f"day_{i}_end")

                        if start_str and end_str:
                            new_avail = Availability(
                                user_id=current_user.id,
                                day_of_week=i,
                                start_time=datetime.strptime(start_str, "%H:%M").time(),
                                end_time=datetime.strptime(end_str, "%H:%M").time(),
                            )
                            db.session.add(new_avail)

                db.session.commit()
                flash("Đã lưu cấu hình lịch làm việc!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Lỗi lưu lịch: {str(e)}", "danger")

    availabilities = Availability.query.filter_by(user_id=current_user.id).all()

    avail_map = {
        a.day_of_week: {"start": a.start_time, "end": a.end_time}
        for a in availabilities
    }

    return render_template("hr/profile.html", avail_map=avail_map)


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
@login_required
def create_interview(app_id):
    # 1. Lấy dữ liệu & Validate quyền
    application = db.session.get(Application, app_id)
    if not application or application.job.company_id != current_user.company_id:
        abort(403)

    start_time_str = request.form.get("start_time")
    location_detail = request.form.get("location_detail")
    location_type = request.form.get("location_type")

    try:
        duration = int(request.form.get("duration", 60))
    except ValueError:
        duration = 60

    # 2. Xử lý thời gian
    try:
        start_time = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M")
    except ValueError:
        flash("Định dạng thời gian không hợp lệ", "danger")
        return redirect(url_for("hr.candidate_view", id=app_id))

    is_conflict, conflict_msg = SchedulerEngine.check_conflict(
        recruiter_id=current_user.id,
        candidate_id=application.user_id,
        start_time=start_time,
        duration_minutes=duration,
    )

    if is_conflict:

        flash(f"⚠️ Không thể lên lịch: {conflict_msg}", "danger")
        return redirect(url_for("hr.candidate_view", id=app_id))

    # 4. Tạo Record
    end_time = start_time + timedelta(minutes=duration)

    final_location = location_detail
    if location_type == "online" and "http" not in location_detail:
        final_location = f"Online: {location_detail}"

    interview = Interview(
        application_id=application.id,
        recruiter_id=current_user.id,
        start_time=start_time,
        end_time=end_time,
        location=final_location,
        meeting_link=location_detail if location_type == "online" else None,
        status="SCHEDULED",
        created_at=datetime.utcnow(),
    )

    db.session.add(interview)
    db.session.commit()

    # 5. Tạo file ICS
    try:
        if location_type == "online" or location_detail:
            ics_filename = ICSGenerator.create_ics_file(interview)
            interview.ics_file_url = ics_filename
            db.session.commit()
    except Exception as e:
        print(f"Lỗi tạo ICS: {e}")

    # 6. Cập nhật trạng thái Application
    if application.status == "NEW":
        application.status = "INTERVIEW"
        db.session.commit()

    # 7. Gửi Email thông báo (Đoạn Code mới thêm)
    try:
        email_sent = send_interview_invitation(application, interview)
        if email_sent:
            flash("✅ Đã lên lịch và gửi email mời phỏng vấn thành công!", "success")
        else:
            flash("⚠️ Đã lên lịch nhưng lỗi khi gửi email.", "warning")
    except Exception as e:
        # Vẫn thông báo thành công việc lên lịch, nhưng báo lỗi mail
        flash(f"⚠️ Đã lên lịch, nhưng lỗi hệ thống gửi mail: {str(e)}", "warning")

    return redirect(url_for("hr.candidate_view", id=app_id))


@hr_bp.route("/applications/<int:app_id>/reject", methods=["POST"])
@login_required
def reject_application(app_id):

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
def analyze_application_cv(app_id):
    """
    Route xử lý khi HR bấm nút 'Phân tích lại'
    """
    try:
        analyzer = CVAnalyzer()

        analyzer.analyze_application(app_id, force_refresh=True)

        flash("Đã phân tích xong!", "success")
    except Exception as e:
        flash(f"Lỗi khi phân tích: {str(e)}", "danger")
        print(f"Error HR Analyze: {e}")

    return redirect(request.referrer)


@hr_bp.route("/api/suggest-slots/<int:app_id>")
@login_required
def get_interview_suggestions(app_id):
    application = db.session.get(Application, app_id)
    if not application:
        return jsonify({"error": "Not found"}), 404

    duration = request.args.get("duration", 60, type=int)

    result = SchedulerEngine.get_suggested_slots(
        recruiter_id=current_user.id,
        candidate_id=application.user_id,
        duration_minutes=duration,
    )

    if isinstance(result, dict) and "error" in result:
        return jsonify(result)

    return jsonify(result)


@hr_bp.route("/interview/update/<int:interview_id>", methods=["POST"])
@login_required
def update_interview(interview_id):
    # Lấy cuộc phỏng vấn cũ
    interview = db.session.get(Interview, interview_id)
    if not interview or interview.recruiter_id != current_user.id:
        abort(403)

    app_id = interview.application_id

    # Lấy dữ liệu form mới
    start_time_str = request.form.get("start_time")
    duration = int(request.form.get("duration", 60))
    location_detail = request.form.get("location_detail")
    location_type = request.form.get("location_type")

    try:
        start_time = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M")
    except ValueError:
        flash("Lỗi định dạng thời gian", "danger")
        return redirect(url_for("hr.candidate_view", id=app_id))

    is_conflict, msg = SchedulerEngine.check_conflict(
        current_user.id,
        interview.application.user_id,
        start_time,
        duration,
        exclude_interview_id=interview.id,  # <--- QUAN TRỌNG
    )

    if is_conflict:
        flash(f"Không thể đổi lịch: {msg}", "danger")
        return redirect(url_for("hr.candidate_view", id=app_id))

    # Cập nhật thông tin
    interview.start_time = start_time
    interview.end_time = start_time + timedelta(minutes=duration)

    final_location = location_detail
    if location_type == "online" and "http" not in location_detail:
        final_location = f"Online: {location_detail}"

    interview.location = final_location
    interview.meeting_link = location_detail if "http" in location_detail else None

    # Regenerate ICS file
    try:
        new_ics = ICSGenerator.create_ics_file(interview)
        interview.ics_file_url = new_ics
    except Exception as e:
        print(f"Lỗi tạo ICS update: {e}")

    db.session.commit()
    flash("Đã cập nhật lịch phỏng vấn!", "success")
    return redirect(url_for("hr.candidate_view", id=app_id))