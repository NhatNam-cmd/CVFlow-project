import os
from app.public import bp
from flask import render_template, request, flash, redirect, current_app
from werkzeug.utils import secure_filename

# Import Repository
from app.repository import get_all_jobs, get_job_by_id, create_candidate, save_cv_file


def allowed_file(filename):
    """Kiểm tra đuôi file hợp lệ (pdf, docx)"""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


@bp.route("/")
@bp.route("/index")
def index():
    """Trang chủ (Danh sách Job)"""
    jobs = get_all_jobs()
    return render_template("public/index.html", title="Trang chủ", jobs=jobs)


@bp.route("/job/<int:job_id>")
def job_detail(job_id):
    """Trang chi tiết Job và Form nộp CV"""
    job = get_job_by_id(job_id)
    if not job:
        return "Job không tồn tại", 404
    return render_template("public/job_detail.html", job=job)


@bp.route("/apply", methods=["POST"])
def apply():
    """Xử lý nộp CV cho Job"""
    job_id = request.form.get("job_id")
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    cv_file = request.files.get("cv_file")

    if cv_file not in request.files:
        flash("Không tìm thấy file", "danger")
        return redirect(request.referrer)

    file = request.files["cv_file"]

    if file.filename == "":
        flash("Chưa chọn file", "danger")
        return redirect(request.referrer)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Lưu file vào thư mục cấu hình (data/uploads)
        file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        # 3. Lưu vào CSDL (Gọi Repository)
        # Bước A: Tạo ứng viên
        new_candidate = create_candidate(name, email, phone)

        # Bước B: Lưu thông tin file (raw_text để trống chờ Module 1 xử lý sau)
        save_cv_file(candidate_id=new_candidate.id, file_path=file_path, raw_text="")

        # (Ghi chú: Logic AI/NLP sẽ được gọi ở đây trong tương lai)

        flash("Nộp hồ sơ thành công! Hệ thống đang xử lý CV của bạn...", "success")
        return render_template("public/apply_success.html", job_id=job_id)
    else:
        flash("File không hợp lệ (Chỉ chấp nhận .pdf, .docx)", "danger")
        return redirect(request.referrer)


# (Thêm các routes public khác ở đây, ví dụ: /job/<id>)
