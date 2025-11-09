from app.public import bp
from flask import render_template


@bp.route("/")
@bp.route("/index")
def index():
    """Trang chủ (Danh sách Job)"""
    # Đây là nơi sẽ code logic để gọi CSDL và lấy Jobs
    # Tạm thời chỉ render template
    return render_template("public/index.html", title="Trang chủ")


# (Thêm các routes public khác ở đây, ví dụ: /job/<id>)
