from app.admin import bp
from app.repository import (
    create_job,
    get_all_jobs,
    get_all_candidates,
    get_candidate_by_id,
)

# Thêm 'session' và 'functools.wraps' để xử lý đăng nhập
from flask import render_template, request, flash, redirect, url_for, session
from config import Config
from functools import wraps


# --- Helper: Decorator để bắt buộc đăng nhập ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Kiểm tra xem trong session có cờ 'admin_logged_in' chưa
        if not session.get("admin_logged_in"):
            flash("Vui lòng đăng nhập để truy cập.", "warning")
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)

    return decorated_function


# --- Routes ---


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Trang Đăng nhập (Đơn giản)"""
    # Nếu đã đăng nhập rồi thì chuyển thẳng vào dashboard
    if session.get("admin_logged_in"):
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        password = request.form.get("password")
        # So sánh mật khẩu
        if password == Config.ADMIN_PASSWORD:
            # QUAN TRỌNG: Lưu trạng thái đăng nhập vào session
            session["admin_logged_in"] = True
            flash("Đăng nhập thành công!", "success")
            return redirect(url_for("admin.dashboard"))
        else:
            flash("Mật khẩu không đúng.", "danger")

    return render_template("admin/login.html", title="Đăng nhập Admin")


@bp.route("/logout")
def logout():
    """Đăng xuất"""
    session.pop("admin_logged_in", None)
    flash("Đã đăng xuất.", "info")
    return redirect(url_for("admin.login"))


@bp.route("/dashboard")
@login_required  # <--- Bảo vệ route này
def dashboard():
    """Dashboard Admin (Danh sách Job)"""
    jobs = get_all_jobs()
    return render_template("admin/dashboard.html", title="Dashboard Admin", jobs=jobs)


@bp.route("/job/new", methods=["POST"])
@login_required  # <--- Bảo vệ route này
def new_job():
    """Tạo Job mới"""
    title = request.form.get("title")
    description = request.form.get("description")
    requirements = request.form.get("requirements")

    if title and description and requirements:
        create_job(title, description, requirements)
        flash("Job mới đã được tạo!", "success")
    else:
        flash("Vui lòng điền đầy đủ thông tin.", "danger")

    return redirect(url_for("admin.dashboard"))


@bp.route("/candidates")
@login_required  # <--- Bảo vệ route này
def candidates():
    """Xem danh sách tất cả ứng viên"""
    candidates = get_all_candidates()
    # Sửa tên file template cho khớp với thư mục đã tạo
    return render_template(
        "admin/job_candidates.html",  # Tận dụng file này để hiển thị list
        title="Tất cả Ứng viên",
        candidates=candidates,
        job=None,  # Truyền job=None để template biết đây là list tổng
    )


@bp.route("/candidate/<int:candidate_id>")
@login_required  # <--- Bảo vệ route này
def candidate_detail(candidate_id):
    """Xem chi tiết ứng viên"""
    candidate = get_candidate_by_id(candidate_id)
    if not candidate:
        flash("Ứng viên không tồn tại.", "danger")
        return redirect(url_for("admin.dashboard"))

    return render_template(
        "admin/candidate_detail.html", title="Chi tiết Ứng viên", candidate=candidate
    )
