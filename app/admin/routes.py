from app.admin import bp
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
    # (Đây là nơi Backend Lead sẽ code logic lấy Jobs từ CSDL)

    # Render template dashboard
    return render_template("admin/dashboard.html", title="Dashboard Admin")


# (có thể thêm các route khác cho admin ở đây sau)
# Ví dụ: /job/<id>/candidates
# Ví dụ: /candidate/<id>
