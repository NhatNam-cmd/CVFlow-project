CVFLOW - SOFTWARE DESIGN DOCUMENT (SDD)
Project Name: CVFlow - AI-Powered Recruitment Platform Version: 1.0 Architecture: Modular Monolith Backend: Python Flask Database: PostgreSQL

MỤC LỤC
Chương 2: Kiến trúc Hệ thống

Chương 3: Cơ sở Dữ liệu

Chương 4: Các luồng Nghiệp vụ Cốt lõi

Chương 5: Triển khai Dịch vụ Nâng cao

Chương 6: Hướng dẫn Dev & Quy trình

CHƯƠNG 2: KIẾN TRÚC HỆ THỐNG
2.1. Kiến trúc Modular Monolith
Dự án được thiết kế theo mô hình Modular Monolith. Mã nguồn nằm trong một Repository duy nhất nhưng được chia tách rõ ràng theo chức năng nghiệp vụ (Vertical Slicing) sử dụng Flask Blueprints.

Phân tầng ứng dụng (Layered Architecture):

Presentation Layer (Templates): Giao diện HTML/CSS/JS (Jinja2).

Web Layer (Blueprints/Controllers): Tiếp nhận Request, Validate Forms, điều hướng.

Service Layer (Business Logic): Xử lý nghiệp vụ phức tạp, AI, tính toán (Pure Python).

Persistence Layer (Models): Tương tác Database (SQLAlchemy).

2.2. Cấu trúc Thư mục
Plaintext

CVFlow/
├── .env                  # Cấu hình môi trường (Secret, DB URL, API Keys)
├── config.py             # Class cấu hình Flask
├── run.py                # Entry Point
├── requirements.txt      # Dependencies
├── Dockerfile            # Cấu hình Deploy
└── app/                  # Mã nguồn chính
    ├── __init__.py       # App Factory
    │
    ├── models/           # DATABASE LAYER
    │   ├── user.py       # User, Company
    │   ├── job.py        # Job, Application, CV
    │   ├── market.py     # MarketData (New)
    │   └── ...
    │
    ├── modules/          # WEB LAYER (Controllers)
    │   ├── auth/         # Login, Register
    │   ├── candidate/    # Ứng viên Dashboard
    │   ├── hr/           # HR Dashboard, Kanban
    │   └── public/       # Landing Page, Job Board
    │
    ├── services/         # SERVICE LAYER (Logic Core & Advanced)
    │   ├── ai_engine/    # Gemini Client, Parsing, Scoring
    │   ├── analytics/    # Gross/Net, Market Stats
    │   └── scheduler/    # Interval Intersection Algorithm
    │
    ├── static/           # CSS, JS, Images, Uploads
    └── templates/        # HTML Files
CHƯƠNG 3: CƠ SỞ DỮ LIỆU
3.1. Sơ đồ Quan hệ Thực thể (ER Diagram)
Tổng quan các bảng trong hệ thống PostgreSQL.

Đoạn mã

erDiagram
    %% --- CORE AUTH & USERS ---
    User {
        int id PK
        string email UK
        string password_hash
        string role "CANDIDATE, HR, ADMIN"
        string full_name
        int company_id FK "Nullable (HR only)"
    }

    Company {
        int id PK
        string name
        string verification_status "PENDING, VERIFIED, REJECTED"
        blob vector_embedding "PickleType (AI)"
        boolean is_active
    }

    %% --- RECRUITMENT MODULE ---
    Job {
        int id PK
        int company_id FK
        int recruiter_id FK
        string title
        float salary_min
        float salary_max
        json skills_required "Automation Config"
        json mini_test_config
        string status "OPEN, CLOSED"
        blob vector_embedding "PickleType (AI)"
    }

    CV_File {
        int id PK
        int user_id FK
        string file_url
        json parsed_skills "AI Extracted"
        blob vector_embedding "PickleType (AI)"
    }

    Application {
        int id PK
        int job_id FK
        int user_id FK "Candidate"
        int cv_id FK
        string status "NEW, INTERVIEW, OFFER, REJECTED"
        int match_score "AI Score"
        string mini_test_answer
    }

    %% --- SCHEDULER MODULE ---
    Availability {
        int id PK
        int user_id FK
        int day_of_week "0=Sun, 1=Mon..."
        time start_time
        time end_time
    }

    Interview {
        int id PK
        int application_id FK
        int recruiter_id FK
        datetime start_time
        datetime end_time
        string meeting_link
        string status "SCHEDULED, COMPLETED"
    }

    %% --- ANALYTICS MODULE ---
    MarketData {
        int id PK
        string job_title_normalized
        float avg_salary_min
        float avg_salary_max
        json top_skills
        datetime updated_at
    }

    %% --- RELATIONSHIPS ---
    Company ||--o{ User : "employees (HR)"
    Company ||--o{ Job : "posts"
    User ||--o{ CV_File : "uploads"
    User ||--o{ Application : "applies"
    User ||--o{ Availability : "defines"
    Job ||--o{ Application : "receives"
    CV_File ||--o{ Application : "snapshot for"
    Application ||--o{ Interview : "has"
CHƯƠNG 4: CÁC LUỒNG NGHIỆP VỤ CỐT LÕI
4.1. Xác thực (Authentication)
4.1.1. Luồng Candidate
Đăng ký -> Active ngay lập tức -> Login -> Dashboard.

4.1.2. Luồng HR (Recruiter)
Đăng ký: Tạo User + Company (Trạng thái PENDING).

Login: Hệ thống kiểm tra Password -> Kiểm tra verification_status.

Nếu PENDING: Chặn Login, hiển thị trang "Chờ duyệt" (Không tạo session).

Nếu VERIFIED: Cho phép Login vào Dashboard.

Duyệt: Admin đổi trạng thái sang VERIFIED.

4.2. Tuyển dụng (Recruitment)
4.2.1. Đăng tin (Job Posting)
HR nhập thông tin Job + Cấu hình Automation (skills_required - JSON tag).

Hệ thống tạo Slug, lưu Job với trạng thái OPEN.

4.2.2. Ứng tuyển (Application)
Actor: Candidate.

Validation:

Job phải đang OPEN.

Check trùng lặp (Một người không nộp 2 lần cho 1 Job).

Check sở hữu CV (Tránh lỗi IDOR - Nộp CV của người khác).

4.3. Quản lý Hồ sơ (Kanban Workflow)
Hỗ trợ quy trình linh hoạt với 4 cột trạng thái:

NEW: Mới nộp (Có điểm AI Match Score).

INTERVIEW: Đã qua lọc, chờ phỏng vấn.

OFFER: Đã trúng tuyển.

REJECTED: Từ chối (Hiển thị mờ).

Tính năng đặc biệt:

Restore: Cho phép khôi phục hồ sơ từ REJECTED về NEW.

Flexible Move: Kéo thả xuôi/ngược tùy ý giữa các cột active.

CHƯƠNG 5: TRIỂN KHAI DỊCH VỤ NÂNG CAO
Thư mục: app/services/

5.1. Analytics: Tính lương Gross/Net
File: analytics/salary_calculator.py

Input: Gross, Vùng, Số người phụ thuộc.

Logic: Áp dụng luật thuế TNCN & BHXH Việt Nam (Cập nhật 2025).

Output: JSON chi tiết (Gross, Net, Thuế, Bảo hiểm) để vẽ biểu đồ.

5.2. Analytics: Market Intelligence
File: analytics/market_analyzer.py

Chiến lược: Backend (Pandas) xử lý số liệu -> JSON -> Frontend (Chart.js/ApexCharts) vẽ.

Nguồn dữ liệu: Hybrid (Ưu tiên bảng MarketData, nếu thiếu thì lấy từ bảng Job nội bộ).

Chức năng:

Salary Benchmark: Min/Max/Avg/Median theo Job Title.

Skill Heatmap: Đếm tần suất kỹ năng yêu cầu.

5.3. AI Engine (Google Gemini)
File: ai_engine/gemini_client.py

Model: gemini-1.5-flash (Nhanh, rẻ).

Tính năng:

CV Parser: PDF -> Text -> JSON (Skills, Exp).

Scoring: So sánh Text CV vs Text JD -> Điểm số (0-100) + Lý do.

Job Suggestion: Tạo Vector Embedding cho CV và Job -> Dùng Cosine Similarity để gợi ý việc làm theo ngữ nghĩa.

5.4. Scheduler (Lập lịch)
File: scheduler/engine.py

Thuật toán: Tìm giao điểm thời gian (Interval Intersection) giữa khung rảnh của HR và Candidate.

Output: Danh sách các slot trống chung.

Export: Tạo file .ics (iCalendar) cho phép người dùng tải về ngay sau khi chốt lịch (Không dùng Email Server).

CHƯƠNG 6: HƯỚNG DẪN DEV & QUY TRÌNH
6.1. Cài đặt (Setup)
Clone code: git clone ...

Môi trường ảo: python -m venv venv -> Activate.

Dependencies: pip install -r requirements.txt.

Database:

Tạo file .env từ mẫu.

Chạy flask db upgrade để tạo bảng.

Run: python run.py.

6.2. Database Migration
Sửa Model -> flask db migrate -m "message" -> Check file migration -> flask db upgrade.

Lưu ý: Không sửa DB bằng tay (pgAdmin).

6.3. Git Workflow
Main: Code ổn định.

Dev: Nhánh phát triển chung.

Feature Branches: feature/ten-tinh-nang.

Luôn pull dev trước khi push. Không commit .env.
