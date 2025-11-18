from app.admin import bp
from app.repository import (
    create_job,
    get_all_jobs,
    get_all_candidates,
    get_candidate_by_id,
)
from flask import render_template, request, flash, redirect, url_for
from config import Config  # Import Config để lấy mật khẩu admin


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Trang Đăng nhập (Đơn giản)"""
    # Đây là logic xử lý mật khẩu hard-coded theo kế hoạch
    if request.method == "POST":
        password = request.form.get("password")
        if password == Config.ADMIN_PASSWORD:
            # (Thêm logic session ở đây sau)
            flash("Đăng nhập thành công!", "success")
            return redirect(url_for("admin.dashboard"))  # Chuyển đến dashboard
        else:
            flash("Mật khẩu không đúng.", "danger")

    return render_template("admin/login.html", title="Đăng nhập Admin")


@bp.route("/dashboard")
def dashboard():
    """Dashboard Admin (Danh sách Job)"""
    jobs = get_all_jobs()
    return render_template("admin/dashboard.html", title="Dashboard Admin", jobs=jobs)


@bp.route("/job/new", methods=["POST"])
def new_job():
    """Tạo Job mới"""
    title = request.form.get("title")
    description = request.form.get("description")
    requirements = request.form.get("requirements")

    if title and description and requirements:
        create_job(title, description, requirements)
        flash("Job mới đã được tạo!", "success")
        return redirect(url_for("admin.dashboard"))
    else:
        flash("Vui lòng điền đầy đủ thông tin.", "danger")

    return redirect(url_for("admin.dashboard"))


@bp.route("/candidates")
def candidates():
    candidates = get_all_candidates()
    return render_template(
        "admin/candidates.html", title="Danh sách Ứng viên", candidates=candidates
    )


@bp.route("/candidate/<int:candidate_id>")
def candidate_detail(candidate_id):
    candidate = get_candidate_by_id(candidate_id)
    if not candidate:
        flash("Ứng viên không tồn tại.", "danger")
        return redirect(url_for("admin.candidates"))
    return render_template(
        "admin/candidate_detail.html", title="Chi tiết Ứng viên", candidate=candidate
    )
