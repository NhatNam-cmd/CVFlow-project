from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
app.secret_key = "preview_secret_key"

# =========================================================================
# 1. MOCK DATA (DỮ LIỆU GIẢ LẬP)
# =========================================================================

MOCK_COMPANIES = [
    {
        "id": 1,
        "name": "FPT Software",
        "logo_url": "https://ui-avatars.com/api/?name=FPT&background=f27124&color=fff",
        "job_count": 120,
        "industry": "Outsourcing",
        "location": "Hà Nội",
    },
    {
        "id": 2,
        "name": "VNG Corporation",
        "logo_url": "https://ui-avatars.com/api/?name=VNG&background=00aefd&color=fff",
        "job_count": 45,
        "industry": "Product",
        "location": "TP.HCM",
    },
    {
        "id": 3,
        "name": "MOMO",
        "logo_url": "https://ui-avatars.com/api/?name=MOMO&background=a50064&color=fff",
        "job_count": 30,
        "industry": "Fintech",
        "location": "TP.HCM",
    },
    {
        "id": 4,
        "name": "Viettel Digital",
        "logo_url": "https://ui-avatars.com/api/?name=Viettel&background=ee0033&color=fff",
        "job_count": 50,
        "industry": "Telco",
        "location": "Hà Nội",
    },
]

MOCK_JOBS = [
    {
        "id": 1,
        "title": "Senior Python Developer",
        "company_name": "FPT Software",
        "location": "Hà Nội",
        "salary_range": "30 - 50 triệu",
        "created_at": "2 giờ trước",
        "match_score": 95,
        "is_hot": True,
        "source": "INTERNAL",
        "skills": ["Python", "Django", "AWS"],
    },
    {
        "id": 2,
        "title": "DevOps Engineer (K8s)",
        "company_name": "VNG Corporation",
        "location": "HCM",
        "salary_range": "Thỏa thuận",
        "created_at": "1 ngày trước",
        "match_score": 88,
        "is_hot": False,
        "source": "TOPDEV",
        "skills": ["Docker", "Kubernetes", "CI/CD"],
    },
    {
        "id": 3,
        "title": "AI Researcher / Data Scientist",
        "company_name": "VinAI",
        "location": "Hà Nội",
        "salary_range": "$3000+",
        "created_at": "3 ngày trước",
        "match_score": 70,
        "is_hot": True,
        "source": "INTERNAL",
        "skills": ["PyTorch", "TensorFlow", "NLP"],
    },
    {
        "id": 4,
        "title": "Backend Golang Senior",
        "company_name": "MOMO",
        "location": "HCM",
        "salary_range": "40 - 60 triệu",
        "created_at": "5 giờ trước",
        "match_score": 92,
        "is_hot": False,
        "source": "INTERNAL",
        "skills": ["Golang", "Microservices", "Redis"],
    },
    {
        "id": 5,
        "title": "Frontend Developer (ReactJS)",
        "company_name": "Tiki",
        "location": "HCM",
        "salary_range": "15 - 25 triệu",
        "created_at": "Hôm qua",
        "match_score": 65,
        "is_hot": False,
        "source": "ITVIEC",
        "skills": ["React", "Redux", "TypeScript"],
    },
]

# =========================================================================
# 2. CẤU HÌNH USER (CHỌN ROLE ĐỂ TEST)
# =========================================================================


class MockUser:
    def __init__(self, role="GUEST", name="Khách vãng lai"):
        self.role = role
        self.full_name = name
        self.is_authenticated = role != "GUEST"
        self.email = "guest@example.com" if role == "GUEST" else "user@cvflow.vn"
        self.company_id = 1 if role == "HR" else None


# 👇 BỎ COMMENT DÒNG DƯỚI ĐÂY ĐỂ ĐỔI VAI TRÒ 👇
current_user = MockUser(role="CANDIDATE", name="Nguyễn Văn A")
# current_user = MockUser(role='HR', name='HR Manager')
# current_user = MockUser(role="ADMIN", name="System Admin")
# current_user = MockUser(role='GUEST', name='Khách vãng lai')

# =========================================================================


@app.context_processor
def inject_user():
    return dict(current_user=current_user, pending_count=5)


def login_required_mock():
    """Chặn Guest truy cập trang nội bộ"""
    if not current_user.is_authenticated:
        return True
    return False


# =========================================================================
# 3. ROUTES
# =========================================================================


# --- PUBLIC ROUTES ---
@app.route("/", endpoint="public.index")
def index():
    # Truyền Mock Data vào trang chủ
    return render_template(
        "public/index.html", jobs=MOCK_JOBS, recommended_jobs=MOCK_JOBS[:3]
    )


@app.route("/job/search", endpoint="public.job_search")
def job_search():
    # Truyền Mock Data vào trang tìm kiếm
    return render_template("public/job_search.html", jobs=MOCK_JOBS)


@app.route("/job/<int:id>", endpoint="public.job_detail")
def job_detail(id):
    # Tìm Job theo ID (Giả lập)
    job = next((j for j in MOCK_JOBS if j["id"] == id), MOCK_JOBS[0])
    return render_template("public/job_detail.html", job=job)


@app.route("/apply", methods=["POST"], endpoint="public.apply")
def apply():
    # Giả lập xử lý nộp đơn thành công
    # Lấy job_id từ form (nếu cần) hoặc mặc định
    return render_template("public/apply_success.html")


# 👆 KẾT THÚC ĐOẠN THÊM 👆


@app.route("/companies", endpoint="public.company_list")
def company_list():
    # Truyền Mock Data vào danh sách công ty
    return render_template("public/company_list.html", companies=MOCK_COMPANIES)


@app.route("/company/<int:id>", endpoint="public.company_detail")
def company_detail(id):
    company = next((c for c in MOCK_COMPANIES if c["id"] == id), MOCK_COMPANIES[0])
    return render_template("public/company_detail.html", company=company)


@app.route("/tools/salary", methods=["GET", "POST"], endpoint="public.salary_tool")
def salary_tool():
    result = None
    if request.method == "POST":
        result = {
            "gross": 20000000,
            "net": 17850000,
            "bhxh": 1600000,
            "bhyt": 300000,
            "bhtn": 200000,
            "income_before_tax": 17900000,
            "tax": 50000,
        }
    return render_template("public/tool_salary.html", result=result)


@app.route("/market-report", endpoint="public.market_report")
def market_report():
    return render_template("public/market_report.html")


# --- AUTH ROUTES ---
@app.route("/login", endpoint="auth.login")
def auth_login():
    return render_template("auth/login.html")


@app.route("/register/candidate", endpoint="auth.register_candidate")
def auth_register_candidate():
    return render_template("auth/register_candidate.html")


@app.route("/register/hr", endpoint="auth.register_hr")
def auth_register_hr():
    return render_template("auth/register_hr.html")


@app.route("/logout", endpoint="auth.logout")
def auth_logout():
    return redirect(url_for("public.index"))


# --- PROTECTED ROUTES (CANDIDATE) ---
@app.route("/candidate/dashboard", endpoint="candidate.dashboard")
def candidate_dashboard():
    if login_required_mock():
        return redirect(url_for("auth.login"))
    return render_template("candidate/dashboard.html")


@app.route("/candidate/profile", endpoint="candidate.profile")
def candidate_profile():
    if login_required_mock():
        return redirect(url_for("auth.login"))
    return render_template("candidate/profile.html")


@app.route("/candidate/cv", endpoint="candidate.cv_manager")
def candidate_cv_manager():
    if login_required_mock():
        return redirect(url_for("auth.login"))
    return render_template("candidate/cv_manager.html")


@app.route("/candidate/jobs", endpoint="candidate.job_manager")
def candidate_job_manager():
    if login_required_mock():
        return redirect(url_for("auth.login"))
    return render_template("candidate/job_manager.html")


@app.route("/candidate/interviews", endpoint="candidate.interview_list")
def candidate_interviews():
    if login_required_mock():
        return redirect(url_for("auth.login"))
    return render_template("candidate/interview_list.html")


# --- PROTECTED ROUTES (HR) ---
@app.route("/hr/dashboard", endpoint="hr.dashboard")
def hr_dashboard():
    if login_required_mock():
        return redirect(url_for("auth.login"))
    return render_template("hr/dashboard.html")


@app.route("/hr/post-job", endpoint="hr.post_job")
def hr_post_job():
    if login_required_mock():
        return redirect(url_for("auth.login"))
    return render_template("hr/post_job.html")


@app.route("/hr/my-jobs", endpoint="hr.my_jobs")
def hr_my_jobs():
    if login_required_mock():
        return redirect(url_for("auth.login"))
    return render_template("hr/my_jobs.html")


@app.route("/hr/candidates", endpoint="hr.candidate_list")
def hr_candidate_list():
    if login_required_mock():
        return redirect(url_for("auth.login"))
    return render_template("hr/candidate_list.html")


@app.route("/hr/candidate/<int:id>", endpoint="hr.candidate_view")
def hr_candidate_view(id):
    if login_required_mock():
        return redirect(url_for("auth.login"))
    return render_template("hr/candidate_view.html")


@app.route("/hr/company", endpoint="hr.company_profile")
def hr_company_profile():
    if login_required_mock():
        return redirect(url_for("auth.login"))
    return render_template("hr/company_profile.html")


@app.route("/hr/schedule", endpoint="hr.schedule_calendar")
def hr_schedule():
    if login_required_mock():
        return redirect(url_for("auth.login"))
    return render_template("hr/schedule_calendar.html")


@app.route("/hr/profile", endpoint="hr.profile")
def hr_profile():
    if login_required_mock():
        return redirect(url_for("auth.login"))
    return render_template("hr/profile.html")


# --- PROTECTED ROUTES (ADMIN) ---
@app.route("/admin/dashboard", endpoint="module.admin.dashboard")
def admin_dashboard():
    if login_required_mock():
        return redirect(url_for("auth.login"))
    return render_template("admin/dashboard.html")


@app.route("/admin/verification", endpoint="module.admin.company_verification")
def admin_verification():
    if login_required_mock():
        return redirect(url_for("auth.login"))
    return render_template("admin/company_verification.html")


@app.route("/admin/crawler", endpoint="module.admin.crawler_manager")
def admin_crawler():
    if login_required_mock():
        return redirect(url_for("auth.login"))
    return render_template("admin/crawler_manager.html")


@app.route("/admin/users", endpoint="module.admin.user_manager")
def admin_users():
    if login_required_mock():
        return redirect(url_for("auth.login"))
    return render_template("admin/user_manager.html")


@app.route("/admin/settings", endpoint="module.admin.settings")
def admin_settings():
    if login_required_mock():
        return redirect(url_for("auth.login"))
    return render_template("admin/settings.html")


@app.route("/admin/profile", endpoint="module.admin.profile")
def admin_profile():
    if login_required_mock():
        return redirect(url_for("auth.login"))
    return render_template("admin/profile.html")


if __name__ == "__main__":
    print("🎨 SERVER PREVIEW V2.0 - ĐANG CHẠY...")
    print(f"👉 Chế độ User hiện tại: {current_user.role}")
    print(f"👉 Dữ liệu Mock: {len(MOCK_JOBS)} jobs, {len(MOCK_COMPANIES)} companies")
    app.run(debug=True, port=5000)
