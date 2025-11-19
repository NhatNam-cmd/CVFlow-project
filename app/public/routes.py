import os
from app.public import bp
from flask import render_template, request, flash, redirect, current_app, url_for
from werkzeug.utils import secure_filename

# Import Repository
# Lưu ý: Cần thêm hàm create_init_score vào repository.py
from app.repository import (
    get_all_jobs,
    get_job_by_id,
    create_candidate,
    save_cv_file,
    create_init_score,
)


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
        # Nên trả về 404 page hoặc redirect về index
        flash("Công việc không tồn tại", "warning")
        return redirect(url_for("public.index"))

    return render_template("public/job_detail.html", job=job)


@bp.route("/apply", methods=["POST"])
def apply():
    """Xử lý nộp CV cho Job"""
    # 1. Nhận dữ liệu từ Form
    job_id = request.form.get("job_id")
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")

    # 2. Kiểm tra File có tồn tại trong request không
    if "cv_file" not in request.files:
        flash("Không tìm thấy file upload", "danger")
        return redirect(request.referrer)

    file = request.files["cv_file"]

    # 3. Kiểm tra người dùng có chọn file không
    if file.filename == "":
        flash("Chưa chọn file", "danger")
        return redirect(request.referrer)

    # 4. Kiểm tra định dạng và Lưu
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

            # --- GIAO TIẾP VỚI REPOSITORY ---

            # Bước A: Tạo ứng viên (Candidate)
            new_candidate = create_candidate(name, email, phone)
            if not new_candidate:
                raise Exception("Lỗi khi tạo ứng viên")

            # Bước B: Lưu thông tin file (CV_File)
            save_cv_file(
                candidate_id=new_candidate.id, file_path=file_path, raw_text=""
            )

            # Bước C (QUAN TRỌNG): Liên kết Ứng viên với Job thông qua bảng Score
            # Điều này xác nhận hành động "Nộp đơn"
            create_init_score(candidate_id=new_candidate.id, job_id=job_id)

            # --- KẾT THÚC GIAO TIẾP ---

            flash("Nộp hồ sơ thành công! Hệ thống đang xử lý CV của bạn...", "success")
            return render_template("public/apply_success.html", job_id=job_id)

        except Exception as e:
            # Log lỗi thực tế ra console để debug
            print(f"Error in /apply: {e}")
            flash("Có lỗi xảy ra khi nộp hồ sơ. Vui lòng thử lại.", "danger")
            return redirect(request.referrer)

    else:
        flash("File không hợp lệ (Chỉ chấp nhận .pdf, .docx)", "danger")
        return redirect(request.referrer)
