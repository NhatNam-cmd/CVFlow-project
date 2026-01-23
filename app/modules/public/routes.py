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
from app.utils.salary_helper import SalaryCalculator
from app.services.analytics.market_analyzer import MarketAnalyzer
from app.models.market import MarketData
import json
from app.services.ai_engine.cv_analyzer import CVAnalyzer
import traceback


@public_bp.route("/")
def index():
    jobs = (
        Job.query.filter_by(is_active=True)
        .order_by(Job.created_at.desc())
        .limit(8)  # Lấy 8 tin cho đẹp grid (4x2)
        .all()
    )

    recommended_jobs = []

    if current_user.is_authenticated and current_user.role == "CANDIDATE":
        main_cv = CV_File.query.filter_by(user_id=current_user.id, is_main=True).first()

        if main_cv and main_cv.vector_embedding:
            ai_results = recommend_jobs_for_cv(main_cv, top_n=3)

            for item in ai_results:
                job_obj = item["job"]
                job_obj.match_score = item["match_score"]
                recommended_jobs.append(job_obj)

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
    keyword = request.args.get("q", "").strip()
    location = request.args.get("location", "All")
    level = request.args.get("level", "All")
    min_salary = request.args.get("min_salary", type=int)
    max_salary = request.args.get("max_salary", type=int)

    page = request.args.get("page", 1, type=int)
    per_page = 10

    query = Job.query.filter(Job.is_active == True)

    if keyword:
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

    query = query.order_by(Job.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    jobs = pagination.items  # Lấy danh sách job của trang hiện tại

    return render_template(
        "public/job_search.html",
        jobs=jobs,  # List job của trang hiện tại
        pagination=pagination,  # Object phân trang để vẽ thanh điều hướng
        total_jobs=pagination.total,  # Tổng số kết quả tìm được
    )


@public_bp.route("/job/<int:id>")
def job_detail(id):
    job = db.session.get(Job, id)
    if not job:
        return render_template("errors/404.html"), 404

    has_applied = False
    user_cvs = []

    if current_user.is_authenticated and current_user.role == "CANDIDATE":
        existing_app = Application.query.filter_by(
            job_id=id, user_id=current_user.id
        ).first()
        if existing_app:
            has_applied = True

        user_cvs = CV_File.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "public/job_detail.html", job=job, has_applied=has_applied, user_cvs=user_cvs
    )


@public_bp.route("/companies")
def company_list():
    keyword = request.args.get("q", "").strip()
    industry = request.args.get("industry", "All")

    query = Company.query.filter_by(verification_status="VERIFIED")

    if keyword:
        query = query.filter(Company.name.ilike(f"%{keyword}%"))

    if industry and industry != "All":
        query = query.filter(Company.industry == industry)

    companies = query.order_by(Company.name).all()

    return render_template("public/company_list.html", companies=companies)


@public_bp.route("/company/<int:id>")
def company_detail(id):
    company = db.session.get(Company, id)
    if not company:
        return render_template("errors/404.html"), 404
    return render_template("public/company_detail.html", company=company)


@public_bp.route("/apply", methods=["POST"])
@login_required
def apply():
    if current_user.role != "CANDIDATE":
        flash("Chỉ ứng viên mới có thể ứng tuyển.", "warning")
        return redirect(url_for("public.index"))

    job_id_raw = request.form.get("job_id")
    cv_id_raw = request.form.get("cv_id")

    if not job_id_raw or not cv_id_raw:
        flash("Dữ liệu không hợp lệ. Vui lòng thử lại.", "danger")
        return redirect(request.referrer or url_for("public.index"))

    try:
        job_id = int(job_id_raw)
        cv_id = int(cv_id_raw)
    except ValueError:
        flash("ID công việc hoặc CV không hợp lệ.", "danger")
        return redirect(url_for("public.index"))

    job = db.session.get(Job, job_id)
    if not job or not job.is_active:
        flash("Công việc này không tồn tại hoặc đã đóng.", "danger")
        return redirect(url_for("public.index"))

    cv = CV_File.query.filter_by(id=cv_id, user_id=current_user.id).first()
    if not cv:
        flash("CV không tồn tại hoặc bạn không có quyền sử dụng CV này.", "danger")
        return redirect(url_for("public.job_detail", id=job_id))

    existing_app = Application.query.filter_by(
        job_id=job_id, user_id=current_user.id
    ).first()
    if existing_app:
        flash("Bạn đã ứng tuyển công việc này rồi.", "warning")
        return redirect(url_for("public.job_detail", id=job_id))

    try:
        print("🚀 [DEBUG] Bắt đầu tạo Application...")
        new_app = Application(
            job_id=job_id,
            user_id=current_user.id,
            cv_id=cv_id,
            status="NEW",
            cover_letter=request.form.get("cover_letter", ""),
            created_at=datetime.utcnow(),
        )
        db.session.add(new_app)
        db.session.commit()
        print(f"✅ [DEBUG] Đã lưu Application ID: {new_app.id}")

        print("🤖 [DEBUG] Chuẩn bị gọi CVAnalyzer...")
        try:
            print(f"🔍 [DEBUG] CVAnalyzer class: {CVAnalyzer}")

            analyzer = CVAnalyzer()
            print(
                "👉 [DEBUG] Init CVAnalyzer thành công. Đang gọi analyze_application..."
            )

            analyzer.analyze_application(new_app.id)
            print("🎉 [DEBUG] AI Chấm điểm XONG!")

        except Exception as ai_error:
            print("🔥 [DEBUG] LỖI AI NGHIÊM TRỌNG:")
            print(f"   Lỗi: {str(ai_error)}")
            print("🔻 Traceback chi tiết:")
            traceback.print_exc()  # In chi tiết dòng nào bị lỗi

        flash("Ứng tuyển thành công! (Check Console xem AI có chạy không)", "success")
        return redirect(url_for("candidate.job_manager"))

    except Exception as e:
        db.session.rollback()
        print(f"☠️ [DEBUG] Lỗi Database: {e}")
        flash(f"Có lỗi xảy ra: {str(e)}", "danger")
        return redirect(url_for("public.job_detail", id=job_id))


@public_bp.route("/tools/salary", methods=["GET", "POST"])
def salary_tool():
    form = SalaryToolForm()
    result = None

    if request.method == "GET":
        pass

    if form.validate_on_submit():
        salary_input = form.gross_salary.data
        dependents = form.dependents.data
        region = int(form.region.data)
        mode = form.calc_mode.data

        if mode == "NET_TO_GROSS":
            result = SalaryCalculator.net_to_gross(
                target_net=salary_input, region_id=region, num_dependents=dependents
            )
        else:
            result = SalaryCalculator.gross_to_net(
                gross_salary=salary_input, region_id=region, num_dependents=dependents
            )

    return render_template("public/tool_salary.html", form=form, result=result)


@public_bp.route("/market-report")
def market_report():
    if MarketData.query.count() == 0:
        analyzer = MarketAnalyzer()
        analyzer.analyze_and_save()

    selected_position = request.args.get("position", "All")

    all_positions = [
        r.job_title_normalized
        for r in MarketData.query.with_entities(
            MarketData.job_title_normalized
        ).distinct()
    ]

    chart_labels = []
    chart_salary = []

    current_data = {
        "salary": 0,
        "demand_score": 0,
        "job_count": 0,
        "competition_ratio": "1:1",
        "competition_text": "Thấp",
        "competition_color": "success",
        "demand_text": "Thấp",
        "demand_color": "secondary",
    }

    if selected_position == "All":
        all_rows = MarketData.query.all()

        agg_data = {}
        total_job_count = 0

        for row in all_rows:
            if row.job_title_normalized not in agg_data:
                agg_data[row.job_title_normalized] = []
            agg_data[row.job_title_normalized].append(row.avg_salary_max)
            total_job_count += row.demand_score  # demand_score đang lưu job_count

        final_list = []
        for title, salaries in agg_data.items():
            avg = sum(salaries) / len(salaries)
            final_list.append({"label": title, "value": avg})

        final_list.sort(key=lambda x: x["value"], reverse=True)
        top_10 = final_list[:10]

        chart_labels = [item["label"] for item in top_10]
        chart_salary = [int(item["value"] / 1000000) for item in top_10]

        if final_list:
            current_data["salary"] = int(
                sum([x["value"] for x in final_list]) / len(final_list)
            )
            current_data["job_count"] = total_job_count
            current_data["demand_text"] = "Toàn thị trường"

    else:
        reports = MarketData.query.filter_by(
            job_title_normalized=selected_position
        ).all()

        level_order = {"FRESHER": 1, "JUNIOR": 2, "MIDDLE": 3, "SENIOR": 4, "LEAD": 5}

        reports.sort(key=lambda x: level_order.get(x.level, 100))

        chart_labels = [r.level for r in reports]
        chart_salary = [int(r.avg_salary_max / 1000000) for r in reports]

        if reports:
            total_sal = sum([r.avg_salary_max for r in reports])
            current_data["salary"] = int(total_sal / len(reports))
            current_data["job_count"] = sum([r.demand_score for r in reports])

            total_market_jobs = (
                db.session.query(func.sum(MarketData.demand_score)).scalar() or 1
            )
            share = (current_data["job_count"] / total_market_jobs) * 100
            score = min(int(share * 5), 100)

            current_data["demand_score"] = score
            if score >= 80:
                current_data["demand_text"], current_data["demand_color"] = (
                    "Rất Cao",
                    "danger",
                )
            elif score >= 50:
                current_data["demand_text"], current_data["demand_color"] = (
                    "Cao",
                    "warning",
                )
            else:
                current_data["demand_text"], current_data["demand_color"] = (
                    "Trung Bình",
                    "primary",
                )

            app_count = (
                Application.query.join(Job)
                .filter(Job.title.ilike(f"%{selected_position.split(' ')[0]}%"))
                .count()
            )
            ratio = round(app_count / max(current_data["job_count"], 1), 1)
            current_data["competition_ratio"] = f"1 : {ratio}"

    rejection_stats = MarketAnalyzer.get_rejection_stats(selected_position)
    reject_labels = list(rejection_stats.keys())
    reject_data = list(rejection_stats.values())

    skill_labels, skill_data = [], []
    sample_report = MarketData.query.filter_by(
        job_title_normalized=(
            selected_position if selected_position != "All" else all_positions[0]
        )
    ).first()
    if sample_report and sample_report.top_skills:
        skill_labels = sample_report.top_skills
        skill_data = [100, 80, 60, 40, 20][: len(skill_labels)]

    return render_template(
        "public/market_report.html",
        all_positions=all_positions,
        selected_position=selected_position,
        current_data=current_data,
        chart_labels=json.dumps(chart_labels),
        chart_salary=json.dumps(chart_salary),
        reject_labels=json.dumps(reject_labels),
        reject_data=json.dumps(reject_data),
        skill_labels=json.dumps(skill_labels),
        skill_data=json.dumps(skill_data),
    )
