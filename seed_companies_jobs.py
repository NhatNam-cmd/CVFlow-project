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
{
        "company": {
            "name": "DevSoft Global Solutions",
            "industry": "Information Technology",
            "address": "Tòa nhà FPT, Phố Duy Tân, Cầu Giấy, Hà Nội",
            "website": "https://devsoft.example.com",
            "description": "Công ty Outsourcing phần mềm top 10 Việt Nam, đối tác của Nhật Bản và Mỹ.",
            "tax_number": "0102223334",
            "logo_url": "company_default.png",
        },
        "hr": {
            "email": "tuyendung@devsoft.com",
            "full_name": "Nguyễn Thị Mai (HR DevSoft)",
            "password": "123",
            "phone": "0988111222",
        },
        "jobs": [
            {
                "title": "Senior Java Developer (Spring Boot)",
                "salary_min": 35000000,
                "salary_max": 55000000,
                "location": "Hà Nội",
                "level": "Senior",
                "description": "Tham gia phát triển dự án Fintech cho khách hàng Nhật Bản. Thiết kế kiến trúc Microservices.",
                "requirements": "5 năm kinh nghiệm Java. Tiếng Nhật N3 là lợi thế (có phụ cấp).",
                "benefits": "Thưởng dự án, Review lương 2 lần/năm, Gói bảo hiểm F-Care.",
                "min_years_experience": 5,
                "skills_required": ["Java", "Spring Boot", "Microservices", "Oracle"],
            },
            {
                "title": "Fresher Automation Tester",
                "salary_min": 8000000,
                "salary_max": 12000000,
                "location": "Hà Nội",
                "level": "Fresher",
                "description": "Viết script test tự động dùng Selenium/Appium. Phối hợp với team Dev để fix bug.",
                "requirements": "Biết lập trình cơ bản (Java/Python). Tư duy logic tốt.",
                "benefits": "Được đào tạo bài bản, lộ trình thăng tiến rõ ràng.",
                "min_years_experience": 0,
                "skills_required": ["Selenium", "Java", "Testing", "Automation"],
            }
        ],
    },

    # 2. NGÂN HÀNG (BANKING & FINTECH)
    {
        "company": {
            "name": "VinaBank Commercial",
            "industry": "Finance & Banking",
            "address": "Quận 1, TP. Hồ Chí Minh",
            "website": "https://vinabank.example.vn",
            "description": "Ngân hàng TMCP hàng đầu với môi trường làm việc chuyên nghiệp và chuyển đổi số mạnh mẽ.",
            "tax_number": "0309998887",
            "logo_url": "company_default.png",
        },
        "hr": {
            "email": "hr.talent@vinabank.vn",
            "full_name": "Lê Tuấn Anh (Talent Acquisition)",
            "password": "123",
            "phone": "0902223334",
        },
        "jobs": [
            {
                "title": "Chuyên viên Quan hệ Khách hàng Doanh nghiệp (RM)",
                "salary_min": 15000000,
                "salary_max": 30000000,
                "location": "Hồ Chí Minh",
                "level": "Mid-Level",
                "description": "Tìm kiếm, thẩm định và duy trì mối quan hệ với khách hàng doanh nghiệp lớn.",
                "requirements": "Tốt nghiệp ĐH Kinh tế/Tài chính. Kỹ năng giao tiếp và đàm phán xuất sắc.",
                "benefits": "Thưởng kinh doanh (Incentive) không giới hạn.",
                "min_years_experience": 2,
                "skills_required": ["Sales", "Corporate Banking", "Risk Assessment", "Communication"],
            },
            {
                "title": "Data Analyst (Khối Quản trị Rủi ro)",
                "salary_min": 25000000,
                "salary_max": 40000000,
                "location": "Hồ Chí Minh",
                "level": "Senior",
                "description": "Phân tích dữ liệu tín dụng, xây dựng mô hình scorecard đánh giá rủi ro.",
                "requirements": "Thành thạo SQL, Python. Ưu tiên ứng viên có chứng chỉ FRM/CFA.",
                "benefits": "Vay lãi suất ưu đãi cho CBNV.",
                "min_years_experience": 3,
                "skills_required": ["SQL", "Python", "Risk Management", "Data Analysis"],
            }
        ],
    },

    # 3. THƯƠNG MẠI ĐIỆN TỬ (E-COMMERCE)
    {
        "company": {
            "name": "ShopNow Vietnam",
            "industry": "E-commerce",
            "address": "Quận Tân Bình, TP. Hồ Chí Minh",
            "website": "https://shopnow.example.vn",
            "description": "Sàn thương mại điện tử chuyên về thời trang và mỹ phẩm phát triển nhanh nhất VN.",
            "tax_number": "0311223344",
            "logo_url": "company_default.png",
        },
        "hr": {
            "email": "recruitment@shopnow.vn",
            "full_name": "Phạm Hương (HR Manager)",
            "password": "123",
            "phone": "0988777666",
        },
        "jobs": [
            {
                "title": "Digital Marketing Manager",
                "salary_min": 40000000,
                "salary_max": 60000000,
                "location": "Hồ Chí Minh",
                "level": "Manager",
                "description": "Hoạch định chiến lược marketing tổng thể. Quản lý ngân sách 5 tỷ/tháng.",
                "requirements": "Có kinh nghiệm chạy Performance Marketing trên các sàn TMĐT.",
                "benefits": "ESOP (Cổ phiếu thưởng) cho nhân sự cấp cao.",
                "min_years_experience": 5,
                "skills_required": ["Digital Marketing", "SEO/SEM", "Leadership", "Performance Marketing"],
            },
            {
                "title": "ReactJS Frontend Developer",
                "salary_min": 20000000,
                "salary_max": 35000000,
                "location": "Hồ Chí Minh",
                "level": "Mid-Level",
                "description": "Tối ưu hóa trải nghiệm người dùng (UX/UI) trên website và mobile web.",
                "requirements": "Thành thạo ReactJS, Redux, NextJS. Có mắt thẩm mỹ tốt.",
                "benefits": "Môi trường trẻ, Happy Hour thứ 6 hàng tuần.",
                "min_years_experience": 2,
                "skills_required": ["ReactJS", "JavaScript", "HTML5/CSS3", "UI/UX"],
            }
        ],
    },

    # 4. GIÁO DỤC (EDUCATION)
    {
        "company": {
            "name": "EduStar English System",
            "industry": "Education & Training",
            "address": "Quận Đống Đa, Hà Nội",
            "website": "https://edustar.example.org",
            "description": "Hệ thống Anh ngữ chuẩn quốc tế với 20 chi nhánh trên toàn quốc.",
            "tax_number": "0105558889",
            "logo_url": "company_default.png",
        },
        "hr": {
            "email": "hr@edustar.org",
            "full_name": "Ms. Sarah (Academic HR)",
            "password": "123",
            "phone": "0944555666",
        },
        "jobs": [
            {
                "title": "Giáo viên Tiếng Anh (IELTS)",
                "salary_min": 20000000,
                "salary_max": 40000000,
                "location": "Hà Nội",
                "level": "Mid-Level",
                "description": "Giảng dạy các lớp IELTS target 6.5+. Chấm bài và feedback cho học viên.",
                "requirements": "IELTS 8.0+. Có chứng chỉ giảng dạy TESOL/CELTA.",
                "benefits": "Thưởng thành tích học viên, du lịch hè.",
                "min_years_experience": 2,
                "skills_required": ["Teaching", "English", "IELTS", "Communication"],
            },
            {
                "title": "Nhân viên Tư vấn Tuyển sinh",
                "salary_min": 8000000,
                "salary_max": 15000000,
                "location": "Hà Nội",
                "level": "Junior",
                "description": "Tư vấn khóa học phù hợp cho phụ huynh và học sinh.",
                "requirements": "Không yêu cầu kinh nghiệm, giọng nói chuẩn, kiên nhẫn.",
                "benefits": "Hoa hồng cao (lên đến 20tr/tháng).",
                "min_years_experience": 0,
                "skills_required": ["Sales", "Consulting", "Customer Service"],
            }
        ],
    },

    # 5. BẤT ĐỘNG SẢN (REAL ESTATE)
    {
        "company": {
            "name": "GreenLand Property Group",
            "industry": "Real Estate",
            "address": "TP. Thủ Đức, TP. Hồ Chí Minh",
            "website": "https://greenland.example.com",
            "description": "Chủ đầu tư các dự án căn hộ cao cấp và nghỉ dưỡng ven biển.",
            "tax_number": "0312345678",
            "logo_url": "company_default.png",
        },
        "hr": {
            "email": "tuyendung@greenland.com",
            "full_name": "Trần Văn Hùng (HR Director)",
            "password": "123",
            "phone": "0909123456",
        },
        "jobs": [
            {
                "title": "Trưởng phòng Kinh doanh BĐS",
                "salary_min": 25000000,
                "salary_max": 50000000,
                "location": "Hồ Chí Minh",
                "level": "Manager",
                "description": "Xây dựng và quản lý đội nhóm sales 15-20 người. Chịu trách nhiệm doanh số.",
                "requirements": "3 năm kinh nghiệm quản lý sàn BĐS. Có sẵn đội nhóm là lợi thế.",
                "benefits": "Thưởng nóng từng căn + Hoa hồng quản lý.",
                "min_years_experience": 3,
                "skills_required": ["Real Estate", "Sales Management", "Leadership", "Training"],
            }
        ],
    },

    # 6. LOGISTICS
    {
        "company": {
            "name": "Mekong Logistics",
            "industry": "Logistics & Supply Chain",
            "address": "Quận Ninh Kiều, Cần Thơ",
            "website": "https://mekonglog.example.com",
            "description": "Nhà cung cấp giải pháp kho bãi và vận chuyển số 1 miền Tây.",
            "tax_number": "1801122334",
            "logo_url": "company_default.png",
        },
        "hr": {
            "email": "hr@mekonglog.com",
            "full_name": "Nguyễn Văn Hậu",
            "password": "123",
            "phone": "0939123123",
        },
        "jobs": [
            {
                "title": "Nhân viên Điều phối Vận tải",
                "salary_min": 10000000,
                "salary_max": 14000000,
                "location": "Cần Thơ",
                "level": "Junior",
                "description": "Sắp xếp lịch trình xe tải, theo dõi lộ trình hàng hóa trên hệ thống GPS.",
                "requirements": "Tốt nghiệp CĐ/ĐH. Sử dụng tốt Excel. Chịu được áp lực thời gian.",
                "benefits": "Phụ cấp ăn trưa, điện thoại.",
                "min_years_experience": 1,
                "skills_required": ["Logistics", "Coordination", "Excel", "Problem Solving"],
            }
        ],
    }
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
