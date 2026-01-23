import os
import re
from datetime import datetime
from app import create_app
from app.extensions import db
from app.models.user import User, Company
from app.models.job import Job


def create_slug(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


seed_data = [
    {
        "company": {
            "name": "TechX Innovations",
            "industry": "Information Technology",
            "address": "Tầng 12, Keangnam Landmark 72, Hà Nội",
            "website": "https://techx.example.com",
            "description": "Công ty công nghệ hàng đầu chuyên về AI và Big Data.",
            "tax_number": "0101234567",
            "logo_url": "company_default.png",
        },
        "hr": {
            "email": "hr.techx@test.com",
            "full_name": "HR Manager TechX",
            "password": "123",
            "phone": "0901000111",
        },
        "jobs": [
            {
                "title": "Senior Python Backend Developer",
                "salary_min": 25000000,
                "salary_max": 45000000,
                "location": "Hà Nội",
                "level": "Senior",  # Map vào cột level
                "description": "Phát triển hệ thống Microservices sử dụng Python (Flask/Django). Loại hình: Full-time.",
                "requirements": "3+ năm kinh nghiệm Python. Có kiến thức về Database Design.",
                "benefits": "MacBook Pro M2, Bảo hiểm Premium.",
                "min_years_experience": 3,
                "skills_required": ["Python", "Django", "Docker"],  # Map vào cột JSON
            },
            {
                "title": "AI Research Intern",
                "salary_min": 5000000,
                "salary_max": 8000000,
                "location": "Hà Nội",
                "level": "Intern",
                "description": "Nghiên cứu các mô hình NLP mới nhất. Loại hình: Internship.",
                "requirements": "Sinh viên năm cuối hoặc mới tốt nghiệp.",
                "benefits": "Cơ hội trở thành nhân viên chính thức.",
                "min_years_experience": 0,
                "skills_required": ["Python", "PyTorch", "NLP"],
            },
        ],
    },
    {
        "company": {
            "name": "Creative Agency Z",
            "industry": "Marketing & Advertising",
            "address": "Quận 1, TP. Hồ Chí Minh",
            "website": "https://agencyz.example.com",
            "description": "Agency sáng tạo với các chiến dịch đạt giải thưởng quốc tế.",
            "tax_number": "0309876543",
            "logo_url": "company_default.png",
        },
        "hr": {
            "email": "hr.agencyz@test.com",
            "full_name": "Talent Acquisition Z",
            "password": "123",
            "phone": "0902000222",
        },
        "jobs": [
            {
                "title": "Digital Marketing Specialist",
                "salary_min": 15000000,
                "salary_max": 25000000,
                "location": "Hồ Chí Minh",
                "level": "Mid-Level",
                "description": "Lên kế hoạch và chạy ads Facebook/Google/TikTok. Loại hình: Full-time.",
                "requirements": "Kinh nghiệm 1-2 năm tại Agency.",
                "benefits": "Thưởng theo dự án.",
                "min_years_experience": 1,
                "skills_required": ["Facebook Ads", "Google Ads", "Content"],
            }
        ],
    },
    {
        "company": {
            "name": "Global Retail Group",
            "industry": "Retail & FMCG",
            "address": "Đà Nẵng",
            "website": "https://globalretail.example.com",
            "description": "Tập đoàn bán lẻ đa quốc gia.",
            "tax_number": "0405556667",
            "logo_url": "company_default.png",
        },
        "hr": {
            "email": "hr.retail@test.com",
            "full_name": "Recruitment Team",
            "password": "123",
            "phone": "0903000333",
        },
        "jobs": [
            {
                "title": "Sales Manager",
                "salary_min": 20000000,
                "salary_max": 35000000,
                "location": "Đà Nẵng",
                "level": "Manager",
                "description": "Quản lý đội ngũ bán hàng 20 người. Loại hình: Full-time.",
                "requirements": "Kỹ năng lãnh đạo, chịu áp lực doanh số tốt.",
                "benefits": "Hoa hồng hấp dẫn, xe đưa đón.",
                "min_years_experience": 5,
                "skills_required": ["Sales", "Leadership", "CRM"],
            }
        ],
    },
]


def run_seed_jobs():
    app = create_app()
    with app.app_context():
        print("🏢 Bắt đầu tạo Công ty, HR và Việc làm...")

        for item in seed_data:
            c_data = item["company"]
            hr_data = item["hr"]
            jobs_list = item["jobs"]

            company = Company.query.filter_by(tax_number=c_data["tax_number"]).first()
            if not company:
                company = Company(
                    name=c_data["name"],
                    slug=create_slug(c_data["name"]),
                    industry=c_data["industry"],
                    address=c_data["address"],
                    website=c_data["website"],
                    description=c_data["description"],
                    tax_number=c_data["tax_number"],
                    logo_url=c_data["logo_url"],
                    verification_status="VERIFIED",
                )
                db.session.add(company)
                db.session.commit()
                print(f"✅ Đã tạo công ty: {company.name}")
            else:
                print(f"ℹ️ Công ty {company.name} đã tồn tại.")

            hr_user = User.query.filter_by(email=hr_data["email"]).first()
            if not hr_user:
                hr_user = User(
                    full_name=hr_data["full_name"],
                    email=hr_data["email"],
                    role="HR",
                    company_id=company.id,
                    phone=hr_data["phone"],
                )
                hr_user.password = hr_data["password"]
                db.session.add(hr_user)
                db.session.commit()
                print(f"   👤 Đã tạo HR Admin: {hr_data['email']}")
            else:
                pass

            for job_info in jobs_list:
                job_slug = create_slug(job_info["title"])
                existing_job = Job.query.filter_by(
                    company_id=company.id, slug=job_slug
                ).first()

                if not existing_job:
                    new_job = Job(
                        title=job_info["title"],
                        slug=job_slug,
                        company_id=company.id,
                        salary_min=job_info["salary_min"],
                        salary_max=job_info["salary_max"],
                        location=job_info["location"],
                        level=job_info.get("level", "Junior"),
                        description=job_info["description"],
                        requirements=job_info["requirements"],
                        benefits=job_info.get("benefits", ""),
                        min_years_experience=job_info.get("min_years_experience", 0),
                        skills_required=job_info.get("skills_required", []),
                        source="INTERNAL",
                        is_active=True,  # Thay vì status='PUBLISHED'
                        created_at=datetime.utcnow(),
                    )
                    db.session.add(new_job)
                    print(f"      💼 Đã đăng tuyển: {job_info['title']}")

            db.session.commit()

        print("\n🎉 Hoàn tất! Bạn có thể test ngay.")


if __name__ == "__main__":
    run_seed_jobs()
