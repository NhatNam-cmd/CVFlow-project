from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
from app.modules.public import public_bp
from app.modules.public.forms import SalaryToolForm
from app.models.job import Job
from app.models.user import Company
from app.models.application import Application, CV_File
from sqlalchemy import func
from sqlalchemy import or_

# --- TRANG CHỦ & TÌM KIẾM ---


@public_bp.route("/")
def index():
    # 1. Lấy Job mới nhất (Giữ nguyên code cũ)
    jobs = (
        Job.query.filter_by(is_active=True)
        .order_by(Job.created_at.desc())
        .limit(6)
        .all()
    )

    # 2. Recommendation (Giữ nguyên code cũ)
    recommended_jobs = []
    if current_user.is_authenticated and current_user.role == "CANDIDATE":
        recommended_jobs = Job.query.filter_by(is_active=True).limit(3).all()

    # 3. LẤY TOP CÔNG TY (LOGIC MỚI)
    # Logic: Lấy cty đã xác thực + Join với bảng Job + Đếm số Job active + Sắp xếp giảm dần
    top_companies = (
        db.session.query(Company)
        .join(Job, Company.id == Job.company_id)
        .filter(Company.verification_status == "VERIFIED")
        .filter(Job.is_active == True)
        .group_by(Company.id)
        .order_by(func.count(Job.id).desc())
        .limit(6)
        .all()
    )

    # Fallback: Nếu chưa có job nào, lấy đại 6 công ty đã xác thực mới nhất
    if not top_companies:
        top_companies = (
            Company.query.filter_by(verification_status="VERIFIED")
            .order_by(Company.created_at.desc())
            .limit(6)
            .all()
        )

    # Truyền biến top_companies ra view
    return render_template(
        "public/index.html",
        jobs=jobs,
        recommended_jobs=recommended_jobs,
        top_companies=top_companies,
    )  # <--- Thêm cái này


@public_bp.route("/job/search")
def job_search():
    # 1. Lấy tham số từ URL
    keyword = request.args.get("q", "").strip()
    location = request.args.get("location", "All")
    level = request.args.get("level", "All")
    min_sal_input = request.args.get("min_salary", type=int)
    max_sal_input = request.args.get("max_salary", type=int)

    # 2. Query cơ bản: Chỉ lấy job đang active
    query = Job.query.filter_by(is_active=True)

    # 3. Áp dụng các bộ lọc

    # Lọc Từ khóa (Tìm trong Title hoặc Kỹ năng)
    if keyword:
        # Dùng ilike để tìm không phân biệt hoa thường
        # Tìm trong Title HOẶC trong mảng Skill (ép kiểu JSON về text để tìm)
        search_term = f"%{keyword}%"
        query = query.filter(
            or_(
                Job.title.ilike(search_term),
                db.cast(Job.skills_required, db.String).ilike(search_term),
            )
        )

    # Lọc Địa điểm
    if location and location != "All":
        query = query.filter(Job.location == location)

    # Lọc Cấp bậc
    if level and level != "All":
        query = query.filter(Job.level == level)

    # Lọc Lương (Logic: Lương Max của job phải lớn hơn Mức Min người dùng tìm)
    # Quy đổi: Người dùng nhập 10 -> Code hiểu là 10.000.000
    if min_sal_input:
        real_min = min_sal_input * 1_000_000
        query = query.filter(Job.salary_max >= real_min)

    if max_sal_input:
        real_max = max_sal_input * 1_000_000
        query = query.filter(Job.salary_min <= real_max)

    # 4. Sắp xếp & Thực thi
    jobs = query.order_by(Job.created_at.desc()).all()

    return render_template("public/job_search.html", jobs=jobs)


# --- CHI TIẾT JOB & CÔNG TY ---


@public_bp.route("/job/<int:id>")
def job_detail(id):
    # Lấy Job theo ID hoặc trả về lỗi 404 nếu không tìm thấy
    job = db.session.get(Job, id)
    if not job:
        return render_template("errors/404.html"), 404

    # Kiểm tra xem ứng viên đã nộp đơn chưa (để disable nút Nộp đơn)
    has_applied = False
    user_cvs = []

    if current_user.is_authenticated and current_user.role == "CANDIDATE":
        # Check Application
        existing_app = Application.query.filter_by(
            job_id=id, user_id=current_user.id
        ).first()
        if existing_app:
            has_applied = True

        # Lấy danh sách CV để hiển thị trong Modal Ứng tuyển
        user_cvs = CV_File.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "public/job_detail.html", job=job, has_applied=has_applied, user_cvs=user_cvs
    )


@public_bp.route("/companies")
def company_list():
    # 1. Lấy tham số tìm kiếm
    keyword = request.args.get("q", "").strip()
    industry = request.args.get("industry", "All")

    # 2. Query cơ bản: Chỉ lấy công ty đã xác thực
    query = Company.query.filter_by(verification_status="VERIFIED")

    # 3. Áp dụng bộ lọc
    if keyword:
        query = query.filter(Company.name.ilike(f"%{keyword}%"))

    if industry and industry != "All":
        query = query.filter(Company.industry == industry)

    # 4. Sắp xếp & Thực thi
    companies = query.order_by(Company.name).all()

    return render_template("public/company_list.html", companies=companies)


@public_bp.route("/company/<int:id>")
def company_detail(id):
    company = db.session.get(Company, id)
    if not company:
        return render_template("errors/404.html"), 404
    return render_template("public/company_detail.html", company=company)


# --- XỬ LÝ ỨNG TUYỂN ---


@public_bp.route("/apply", methods=["POST"])
@login_required
def apply():
    """Xử lý khi ứng viên bấm nút 'Gửi Hồ Sơ'"""
    # Chỉ Candidate mới được nộp
    if current_user.role != "CANDIDATE":
        flash("Tài khoản Nhà tuyển dụng không thể nộp đơn.", "warning")
        return redirect(request.referrer)

    job_id = request.form.get("job_id")
    cv_id = request.form.get("cv_id")  # Lấy ID của CV đã chọn trong Modal

    if not job_id or not cv_id:
        flash("Dữ liệu không hợp lệ.", "danger")
        return redirect(request.referrer)

    # Kiểm tra nộp trùng
    exists = Application.query.filter_by(job_id=job_id, user_id=current_user.id).first()
    if exists:
        flash("Bạn đã ứng tuyển công việc này rồi!", "info")
        return redirect(url_for("public.job_detail", id=job_id))

    # Tạo Application mới
    new_app = Application(
        job_id=job_id,
        user_id=current_user.id,
        cv_id=cv_id,
        status="NEW",
        match_score=0,  # Sẽ được AI update sau (Feature 5)
    )

    db.session.add(new_app)
    db.session.commit()

    # TODO: Trigger Celery Task để AI chấm điểm (sẽ làm ở phần Services)

    return render_template("public/apply_success.html")


# --- CÔNG CỤ TIỆN ÍCH ---


@public_bp.route("/tools/salary", methods=["GET", "POST"])
def salary_tool():
    form = SalaryToolForm()
    result = None

    if form.validate_on_submit():
        # Gọi Service tính lương (Pure Python)
        # Chúng ta sẽ tạo file services/analytics/salary.py sau
        # Tạm thời để logic giả lập ở đây để test UI
        gross = form.gross_salary.data
        net = gross * 0.895  # Giả lập trừ 10.5% bảo hiểm
        result = {
            "gross": gross,
            "net": net,
            "bhxh": gross * 0.08,
            "bhyt": gross * 0.015,
            "bhtn": gross * 0.01,
            "income_before_tax": gross - (gross * 0.105),
            "tax": 0,  # Tạm tính
        }

    return render_template("public/tool_salary.html", form=form, result=result)


@public_bp.route("/market-report")
def market_report():
    # Trang này sẽ gọi API để vẽ biểu đồ JS
    return render_template("public/market_report.html")
