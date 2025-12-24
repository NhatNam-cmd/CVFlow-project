import time
from app import create_app, db
from app.models import User, Company, Job

# Import đúng hàm embedding mới (Google GenAI)
from app.services.ai_engine.gemini_client import get_text_embedding

app = create_app()

# Dữ liệu mẫu phong phú
SAMPLE_JOBS = [
    {
        "title": "Senior Python Backend Developer",
        "desc": "Phát triển hệ thống Backend hiệu năng cao dùng Python, Django, PostgreSQL. "
        "Xây dựng RESTful APIs chuẩn.",
        "reqs": "5+ năm kinh nghiệm Python. Rất giỏi Django/FastAPI."
        " Kiến thức sâu về Database (PostgreSQL, Redis).",
        "level": "SENIOR",
        "salary_min": 40000000,
        "salary_max": 70000000,
    },
    {
        "title": "Java Spring Boot Engineer",
        "desc": "Tham gia dự án Core Banking. Xây dựng Microservices với Spring Boot, Kafka.",
        "reqs": "Thành thạo Java Core, Spring Framework. Kinh nghiệm làm việc với hệ thống phân tán.",
        "level": "MIDDLE",
        "salary_min": 25000000,
        "salary_max": 45000000,
    },
    {
        "title": "Frontend Developer (ReactJS)",
        "desc": "Phát triển giao diện web app thương mại điện tử. Tối ưu trải nghiệm người dùng (UX/UI).",
        "reqs": "Thành thạo JavaScript (ES6+), ReactJS, Redux Toolkit. Có tư duy thẩm mỹ tốt.",
        "level": "JUNIOR",
        "salary_min": 15000000,
        "salary_max": 25000000,
    },
    {
        "title": "DevOps Engineer (AWS/K8s)",
        "desc": "Thiết lập và vận hành CI/CD pipeline. Quản lý hạ tầng trên AWS.",
        "reqs": "Kinh nghiệm với Docker, Kubernetes, Jenkins, Terraform. Scripting (Bash/Python).",
        "level": "SENIOR",
        "salary_min": 50000000,
        "salary_max": 90000000,
    },
    {
        "title": "AI Research Engineer (NLP)",
        "desc": "Nghiên cứu và phát triển các model xử lý ngôn ngữ tự nhiên (LLM).",
        "reqs": "Thành thạo Python, PyTorch/TensorFlow. Kiến thức sâu về Machine Learning, Transformers.",
        "level": "MIDDLE",
        "salary_min": 35000000,
        "salary_max": 65000000,
    },
    {
        "title": "Manual Tester / QA",
        "desc": "Kiểm thử chức năng website và mobile app. Viết test case và log bug.",
        "reqs": "Cẩn thận, tỉ mỉ. Biết SQL cơ bản để query dữ liệu test.",
        "level": "FRESHER",
        "salary_min": 8000000,
        "salary_max": 12000000,
    },
]


def seed_data():
    with app.app_context():
        print("🚀 Bắt đầu khởi tạo dữ liệu mẫu...")

        # 1. TẠO CÔNG TY (Nếu chưa có)
        company = Company.query.filter_by(name="Tech Corp Demo").first()
        if not company:
            company = Company(
                name="Tech Corp Demo",
                slug="tech-corp-demo",
                verification_status="VERIFIED",
                logo_url="https://ui-avatars.com/api/?name=Tech+Corp&background=0D8ABC&color=fff",
                address="Tòa nhà Bitexco, Q1, TP.HCM",
                industry="Information Technology",
                tax_number="0101234567",
            )
            db.session.add(company)
            db.session.commit()
            print("✅ Đã tạo Company: Tech Corp Demo")

        # 2. TẠO HR USER (Nếu chưa có)
        hr_user = User.query.filter_by(email="hr_demo@cvflow.com").first()
        if not hr_user:
            hr_user = User(
                full_name="HR Manager Demo",
                email="hr_demo@cvflow.com",
                role="HR",
                password="password123",  # Setter sẽ hash
                company_id=company.id,  # User thuộc về Company này
            )
            db.session.add(hr_user)
            db.session.commit()
            print("✅ Đã tạo HR User: hr_demo@cvflow.com")
        else:
            # Đảm bảo HR này thuộc về công ty demo
            if not hr_user.company_id:
                hr_user.company_id = company.id
                db.session.commit()

        # 3. TẠO JOBS VÀ VECTOR EMBEDDING
        print("\n⏳ Đang tạo Job và gọi Google AI (Embedding)...")

        # Tạo 2 lượt để có nhiều dữ liệu (khoảng 12 jobs)
        for i in range(2):
            for template in SAMPLE_JOBS:
                job_title = f"{template['title']} ({i+1})"

                # Check trùng
                if Job.query.filter_by(title=job_title).first():
                    print(f"   Skip: {job_title}")
                    continue

                # Tạo Job Object
                job = Job(
                    title=job_title,
                    description=template["desc"],
                    requirements=template["reqs"],
                    salary_min=template["salary_min"],
                    salary_max=template["salary_max"],
                    currency="VND",
                    location="Hồ Chí Minh",
                    level=template["level"],
                    is_active=True,
                    company_id=company.id,
                    recruiter_id=hr_user.id,  # Người đăng tin
                    skills_required=template["skills"],
                )

                # --- QUAN TRỌNG: TẠO VECTOR ---
                full_text = f"{job.title}. {job.description}. {job.requirements}"
                vector = get_text_embedding(full_text)

                if vector:
                    job.vector_embedding = vector
                    print(f"   + Created & Embedded: {job_title}")
                else:
                    print(f"   - Created (No Vector - API Error): {job_title}")

                db.session.add(job)
                time.sleep(1)  # Tránh rate limit

            db.session.commit()

        print("\n🎉 XONG! Dữ liệu mẫu đã sẵn sàng.")


if __name__ == "__main__":
    seed_data()
