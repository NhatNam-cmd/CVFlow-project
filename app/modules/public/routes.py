from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
from app.modules.public import public_bp
from app.modules.public.forms import SalaryToolForm
from app.models.application import Application
from sqlalchemy import func
from datetime import datetime
from app.models import Job, Company, CV_File
from app.services.ai_engine.recommender import recommend_jobs_for_cv  # Import hàm gợi ý
from app.models.market import MarketData
from app.services.analytics.market_analyzer import MarketAnalyzer
import json

# --- TRANG CHỦ & TÌM KIẾM ---


@public_bp.route("/")
def index():
    # ==========================================
    # 1. LẤY VIỆC LÀM MỚI NHẤT (Cho phần "Việc làm mới nhất")
    # ==========================================
    jobs = (
        Job.query.filter_by(is_active=True)
        .order_by(Job.created_at.desc())
        .limit(8)  # Lấy 8 tin cho đẹp grid (4x2)
        .all()
    )

    # ==========================================
    # 2. XỬ LÝ GỢI Ý VIỆC LÀM TỪ AI (Cho Candidate)
    # ==========================================
    recommended_jobs = []

    if current_user.is_authenticated and current_user.role == "CANDIDATE":
        # Tìm CV chính của user
        main_cv = CV_File.query.filter_by(user_id=current_user.id, is_main=True).first()

        # Chỉ chạy AI nếu CV chính có vector embedding
        if main_cv and main_cv.vector_embedding:
            # Gọi hàm gợi ý AI (Lấy top 3 để hiện trang chủ)
            # Hàm này trả về list dict: [{'job': job_obj, 'match_score': 85}, ...]
            ai_results = recommend_jobs_for_cv(main_cv.vector_embedding, top_n=3)

            # Xử lý dữ liệu để truyền sang template
            for item in ai_results:
                job_obj = item["job"]
                # Gán match_score vào object job để hiển thị trên giao diện
                job_obj.match_score = item["match_score"]
                recommended_jobs.append(job_obj)

    # ==========================================
    # 3. LẤY TOP CÔNG TY (LOGIC CỦA BẠN)
    # Logic: Lấy cty đã xác thực + Join với bảng Job + Đếm số Job active + Sắp xếp giảm dần
    # ==========================================
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

    return render_template(
        "public/index.html",
        jobs=jobs,
        top_companies=top_companies,  # Danh sách công ty nổi bật
        recommended_jobs=recommended_jobs,  # Danh sách việc làm AI gợi ý
    )


@public_bp.route("/jobs")
def job_search():
    # 1. Lấy tham số từ URL
    keyword = request.args.get("q", "").strip()
    location = request.args.get("location", "All")
    level = request.args.get("level", "All")
    min_salary = request.args.get("min_salary", type=int)
    max_salary = request.args.get("max_salary", type=int)

    # Tham số phân trang (Mặc định trang 1, 10 job/trang)
    page = request.args.get("page", 1, type=int)
    per_page = 10

    # 2. Xây dựng Query cơ bản
    query = Job.query.filter(Job.is_active == True)

    # 3. Áp dụng bộ lọc (Filter)
    if keyword:
        # Tìm kiếm trong tiêu đề hoặc mô tả (Case-insensitive)
        query = query.filter(
            (Job.title.ilike(f"%{keyword}%")) | (Job.description.ilike(f"%{keyword}%"))
        )

    if location and location != "All":
        query = query.filter(Job.location.ilike(f"%{location}%"))

    if level and level != "All":
        query = query.filter(Job.level.ilike(f"%{level}%"))

    if min_salary:
        query = query.filter(Job.salary_min >= min_salary * 1000000)  # Đổi sang triệu

    if max_salary:
        query = query.filter(Job.salary_max <= max_salary * 1000000)

    # 4. Sắp xếp (Mới nhất lên đầu)
    query = query.order_by(Job.created_at.desc())

    # 5. PHÂN TRANG (Quan trọng)
    # Thay vì .all(), ta dùng .paginate()
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    jobs = pagination.items  # Lấy danh sách job của trang hiện tại

    return render_template(
        "public/job_search.html",
        jobs=jobs,  # List job của trang hiện tại
        pagination=pagination,  # Object phân trang để vẽ thanh điều hướng
        total_jobs=pagination.total,  # Tổng số kết quả tìm được
    )


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
    # 1. Kiểm tra quyền (chỉ Candidate được ứng tuyển)
    if current_user.role != "CANDIDATE":
        flash("Chỉ ứng viên mới có thể ứng tuyển.", "warning")
        return redirect(url_for("public.index"))

    # 2. Lấy dữ liệu thô
    job_id_raw = request.form.get("job_id")
    cv_id_raw = request.form.get("cv_id")

    # 3. Validate cơ bản: Kiểm tra rỗng
    if not job_id_raw or not cv_id_raw:
        flash("Dữ liệu không hợp lệ. Vui lòng thử lại.", "danger")
        return redirect(request.referrer or url_for("public.index"))

    try:
        # 4. Validate kiểu dữ liệu (Phải là số nguyên)
        job_id = int(job_id_raw)
        cv_id = int(cv_id_raw)
    except ValueError:
        flash("ID công việc hoặc CV không hợp lệ.", "danger")
        return redirect(url_for("public.index"))

    # 5. Validate logic: Job có tồn tại và đang mở không?
    job = db.session.get(
        Job, job_id
    )  # Dùng db.session.get thay vì Job.query.get (SQLAlchemy 2.0 style)
    if not job or not job.is_active:
        flash("Công việc này không tồn tại hoặc đã đóng.", "danger")
        return redirect(url_for("public.index"))

    # 6. Validate logic: CV có tồn tại và CÓ PHẢI CỦA USER NÀY KHÔNG? (Quan trọng)
    cv = CV_File.query.filter_by(id=cv_id, user_id=current_user.id).first()
    if not cv:
        flash("CV không tồn tại hoặc bạn không có quyền sử dụng CV này.", "danger")
        return redirect(url_for("public.job_detail", id=job_id))

    # 7. Validate logic: Đã nộp đơn chưa?
    existing_app = Application.query.filter_by(
        job_id=job_id, user_id=current_user.id
    ).first()
    if existing_app:
        flash("Bạn đã ứng tuyển công việc này rồi.", "warning")
        return redirect(url_for("public.job_detail", id=job_id))

    # --- NẾU VƯỢT QUA HẾT CÁC ẢI TRÊN THÌ MỚI LƯU ---
    try:
        new_app = Application(
            job_id=job_id,
            user_id=current_user.id,
            cv_id=cv_id,  # Lưu ID CV đã chọn
            status="NEW",
            created_at=datetime.utcnow(),
        )
        db.session.add(new_app)
        db.session.commit()

        flash("Ứng tuyển thành công! Nhà tuyển dụng sẽ sớm liên hệ với bạn.", "success")
        return redirect(
            url_for("candidate.job_manager")
        )  # Chuyển hướng về trang quản lý việc làm

    except Exception as e:
        db.session.rollback()
        flash(f"Có lỗi xảy ra: {str(e)}", "danger")
        return redirect(url_for("public.job_detail", id=job_id))


# --- CÔNG CỤ TIỆN ÍCH ---


@public_bp.route("/tools/salary", methods=["GET", "POST"])
def salary_tool():
    form = SalaryToolForm()
    result = None

    if form.validate_on_submit():
        # Gọi Service tính lương (Pure Python)
        # Chúng ta sẽ tạo file services/analytics/salary_calculator.py sau
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
    # 1. Kiểm tra xem đã có báo cáo trong DB chưa
    existing_report_count = MarketData.query.count()

    # 2. Nếu chưa có dòng nào -> Mới gọi AI chạy phân tích
    if existing_report_count == 0:
        print("⚡ Data not found. Running AI Analysis...")
        analyzer = MarketAnalyzer()
        analyzer.analyze_and_save()

    # 3. Lấy dữ liệu báo cáo (Lúc này chắc chắn đã có)
    reports = MarketData.query.order_by(MarketData.avg_salary_max.desc()).all()

    # 4. Lấy thống kê từ chối (Gọi qua Static Method, rất nhanh)
    rejection_stats = MarketAnalyzer.get_rejection_stats()

    # --- PHẦN DƯỚI GIỮ NGUYÊN ---
    # Chuẩn bị dữ liệu biểu đồ
    chart_labels = [r.job_title_normalized for r in reports]
    chart_salary = [int(r.avg_salary_max / 1000000) for r in reports]

    reject_labels = list(rejection_stats.keys())
    reject_data = list(rejection_stats.values())

    # Fake data skill demo
    skill_labels = reports[0].top_skills if reports else []
    skill_data = [10, 8, 6, 5, 4]

    return render_template(
        "public/market_report.html",
        reports=reports,
        chart_labels=json.dumps(chart_labels),
        chart_salary=json.dumps(chart_salary),
        reject_labels=json.dumps(reject_labels),
        reject_data=json.dumps(reject_data),
        skill_labels=json.dumps(skill_labels),
        skill_data=json.dumps(skill_data),
    )
