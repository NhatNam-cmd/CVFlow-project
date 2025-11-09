
Chào nhóm,

Repo chính thức cho dự án **"CVFlow"** của chúng ta đã được thiết lập và sẵn sàng để phát triển.

Với vai trò là DevOps/QA Lead, mình đã hoàn thành việc thiết lập **"bộ móng" (foundation)** và **"bộ xương" (skeleton)** của dự án. Điều này đảm bảo rằng:

1. Chúng ta có một môi trường làm việc nhất quán.
    
2. Chất lượng code được kiểm soát tự động.
    
3. Cấu trúc dự án tuân thủ Sơ đồ Kiến trúc Phân lớp mà chúng ta đã thống nhất.
    

Tài liệu này giải thích những gì mình **đã làm** và những gì mọi người cần làm **ngay bây giờ** để bắt đầu code.

---

### 1. 🏗️ Những gì ĐÃ HOÀN THÀNH (Phần của DevOps Lead)

Mình đã push "bộ xương" của ứng dụng lên nhánh `main`. Repo hiện tại đã bao gồm:

- **Toàn bộ Cấu trúc Thư mục:** Đã tạo tất cả các thư mục (`app/`, `app/admin/`, `app/public/`, `app/services/`, `app/templates/`, `docs/`, `tests/`) theo đúng cấu trúc 5 lớp của Sơ đồ Kiến trúc.
    
- **Thiết lập QA (Luật chơi):**
    
    - `.gitignore`: Đã cấu hình để bỏ qua `.venv/`, `.db`, `data/`, `uploads/`.
        
    - `.flake8`: Đã cấu hình để tương thích với `black`.
        
    - `.pre-commit-config.yaml`: Đã cài đặt hook cho `black` và `flake8`.
        
- **Thiết lập Thư viện (`requirements.txt`):**
    
    - Đã thêm các thư viện "cốt lõi" cho MVP: `Flask`, `Flask-SQLAlchemy`, `PyPDF2`, `python-docx`, `nltk`, `scikit-learn`, `numpy`.
        
- **Thiết lập Flask Core (Nền tảng):**
    
    - `config.py`: Đã viết code cấu hình (Database URI, Admin Password, Upload Folder).
        
    - `app/__init__.py`: Đã viết hàm `create_app()` (Application Factory), đăng ký Blueprints, và tự động gọi `db.create_all()`.
        
    - `run.py`: Đã viết file chạy chính.
        
- **Thiết lập CSDL (Lớp Entity):**
    
    - `app/models.py`: Đã code **toàn bộ 5 bảng CSDL** (`Job`, `Candidate`, `CV_File`, `Extracted_Skill`, `Score`) dựa trên Sơ đồ ERD.
        
- **Thiết lập Routes (Bộ xương Luồng):**
    
    - `app/public/routes.py` và `app/admin/routes.py`: Đã viết code "xương" cho các route chính (`/`, `/login`, `/dashboard`).
        
- **Thiết lập Giao diện:**
    
    - `app/templates/`: Đã tạo tất cả các file HTML trống cần thiết cho cả 2 Luồng (Public và Admin).
        
- **Tài liệu:** Đã tạo thư mục `docs/` và upload Bản Hiến Chương. _(Lưu ý: các file .svg sơ đồ đang trống, mình sẽ cập nhật sau)._
    

---

### 2. 🚀 Hướng dẫn Bắt đầu (Việc các bạn cần làm NGAY)

Để bắt đầu làm việc, mọi người cần thực hiện **6 BƯỚC BẮT BUỘC** sau để đồng bộ môi trường:

1. **Clone Repo:** Mở terminal, `cd` vào thư mục bạn muốn chứa dự án, và chạy:
    
    Bash
    
    ```
    git clone https://github.com/[Tên_Repo_Của_Bạn]/CVFlow-project.git
    cd CVFlow-project
    ```
    
2. **Tạo Môi trường ảo (Venv):** (Chúng ta đã thống nhất dùng **Python 3.9**)
    
    Bash
    
    ```
    py -3.9 -m venv .venv
    ```
    
3. **Kích hoạt Venv:**
    
    - (Trên Git Bash): `source .venv/Scripts/activate`
        
    - (Trên CMD/PowerShell): `.venv\Scripts\activate`
        
4. **Cài đặt Thư viện:**
    
    Bash
    
    ```
    pip install -r requirements.txt
    ```
    
5. **CÀI ĐẶT "CHỐT CHẶN" QA (BẮT BUỘC):**
    
    - Lệnh này chỉ chạy 1 lần duy nhất. Nó sẽ cài đặt `pre-commit` vào Git của bạn để tự động kiểm tra code (chạy `black` và `flake8`) mỗi khi bạn `commit`.
        
    
    Bash
    
    ```
    pre-commit install
    ```
    
6. **Chạy Thử Ứng dụng:**
    
    Bash
    
    ```
    python run.py
    ```
    
    - Nếu bạn thấy server Flask khởi động, tức là bạn đã setup thành công! Ứng dụng sẽ tự động tạo file `data/cvflow.db` (do file `.gitignore` bỏ qua nên sẽ không có sẵn trên repo).
        

---

### 3. 🎯 Nhiệm vụ Tiếp theo (Bắt đầu Code!)

Bây giờ, mọi người hãy bắt đầu làm việc theo **Lộ trình 12 tuần** (xem trong `docs/`).

**Quy trình làm việc (Bắt buộc):**

1. Luôn `git checkout main` và `git pull origin main` trước khi bắt đầu.
    
2. Tạo nhánh mới: `git checkout -b feature/[tên-tính-năng]` (ví dụ: `feature/build-module-1-parser`).
    
3. Code tính năng.
    
4. `git add .` và `git commit -m "..."`.
    
    - (Nếu `pre-commit` báo `Failed`, hãy `git add .` lại và `commit` lần nữa).
        
5. `git push origin feature/[tên-tính-năng]`.
    
6. Tạo **Pull Request (PR)** trên GitHub và tag các thành viên khác vào review.
    

**Phân công theo Lộ trình (Tuần 1-4):**

- **Backend Lead (Lead A):**
    
    - Bắt đầu hoàn thiện logic API trong `app/admin/routes.py` (ví dụ: code `POST /job`).
        
    - Bắt đầu viết code cho `app/repository.py` (logic truy vấn CSDL).
        
- **NLP Lead (Lead B):**
    
    - Bắt đầu nghiên cứu và code **Module 1** (Xử lý File) và **Module 2** (NER) trong các file (đang trống) thuộc `app/services/`.
        
- **Frontend Lead (Lead C):**
    
    - Bắt đầu code giao diện HTML/CSS (dùng template) cho các file trong `app/templates/public/` và `app/templates/admin/`.
        
    - Code JavaScript để gọi các API (ví dụ: `GET /jobs`).
        
- **DevOps/QA Lead (Lead D - Tôi):**
    
    - Mình sẽ bắt đầu viết Unit Test cho các module trong thư mục `tests/` và hỗ trợ mọi người về Git/PR.
        

Hãy nhớ triết lý "Sở hữu chung" của chúng ta. Mọi người đều có thể (và nên) tham gia code các module Python trong `app/services/`.
