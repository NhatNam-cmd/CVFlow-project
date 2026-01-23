import time
from app import create_app, db
from app.models import User, Company, Job

from app.services.ai_engine.gemini_client import get_text_embedding

app = create_app()

SAMPLE_JOBS = [
    {
        "company": {
            "name": "FinSmart Solutions",
            "industry": "Finance & Banking",
            "address": "Quận Hoàn Kiếm, Hà Nội",
            "website": "https://finsmart.example.com",
            "description": "Giải pháp tài chính thông minh 4.0, ví điện tử và thanh toán số.",
            "tax_number": "0109988776",
            "logo_url": "company_default.png",
        },
        "hr": {
            "email": "hr.finsmart@test.com",
            "full_name": "Recruiter FinSmart",
            "password": "123",
            "phone": "0911222333",
        },
        "jobs": [
            {
                "title": "Data Analyst (Finance)",
                "salary_min": 18000000,
                "salary_max": 30000000,
                "location": "Hà Nội",
                "level": "Mid-Level",
                "description": "Phân tích dữ liệu giao dịch, phát hiện gian lận (Fraud Detection).",
                "requirements": "Thành thạo SQL, Python (Pandas), trực quan hóa dữ liệu (Tableau/PowerBI).",
                "benefits": "Bảo hiểm sức khỏe toàn diện, thưởng quý.",
                "min_years_experience": 2,
                "skills_required": ["SQL", "Python", "Tableau", "Data Analysis"],
            },
            {
                "title": "Senior Java Developer",
                "salary_min": 35000000,
                "salary_max": 60000000,
                "location": "Hà Nội",
                "level": "Senior",
                "description": "Xây dựng hệ thống Core Banking chịu tải cao. Microservices.",
                "requirements": "5+ năm kinh nghiệm Java/Spring Boot. Hiểu sâu về Oracle/PostgreSQL.",
                "benefits": "Signing bonus 1 tháng lương.",
                "min_years_experience": 5,
                "skills_required": ["Java", "Spring Boot", "Microservices", "SQL"],
            }
        ],
    },
    {
        "company": {
            "name": "E-Shop Vietnam",
            "industry": "E-commerce",
            "address": "Quận Tân Bình, TP. Hồ Chí Minh",
            "website": "https://eshop.example.vn",
            "description": "Sàn thương mại điện tử chuyên về thời trang và mỹ phẩm.",
            "tax_number": "0311223344",
            "logo_url": "company_default.png",
        },
        "hr": {
            "email": "tuyendung@eshop.vn",
            "full_name": "E-Shop HR Team",
            "password": "123",
            "phone": "0988777666",
        },
        "jobs": [
            {
                "title": "ReactJS Frontend Developer",
                "salary_min": 15000000,
                "salary_max": 25000000,
                "location": "Hồ Chí Minh",
                "level": "Junior",
                "description": "Phát triển giao diện người dùng website TMĐT. Tối ưu trải nghiệm UX/UI.",
                "requirements": "Có kinh nghiệm ReactJS, Redux. Biết cắt HTML/CSS chuẩn.",
                "benefits": "Môi trường trẻ trung, Happy Hour hàng tuần.",
                "min_years_experience": 1,
                "skills_required": ["ReactJS", "JavaScript", "HTML/CSS", "Git"],
            },
            {
                "title": "Product Owner",
                "salary_min": 30000000,
                "salary_max": 50000000,
                "location": "Hồ Chí Minh",
                "level": "Manager",
                "description": "Làm việc với team Tech và Business để định hướng phát triển sản phẩm App Mobile.",
                "requirements": "Tư duy sản phẩm tốt, kỹ năng giao tiếp, hiểu quy trình Agile/Scrum.",
                "benefits": "ESOP (Cổ phiếu thưởng).",
                "min_years_experience": 4,
                "skills_required": ["Product Management", "Agile", "Scrum", "Jira"],
            }
        ],
    },
    {
        "company": {
            "name": "Green Edu System",
            "industry": "Education & Training",
            "address": "Quận Cầu Giấy, Hà Nội",
            "website": "https://greenedu.example.org",
            "description": "Hệ thống giáo dục trực tuyến và đào tạo kỹ năng mềm.",
            "tax_number": "0105558889",
            "logo_url": "company_default.png",
        },
        "hr": {
            "email": "hr@greenedu.org",
            "full_name": "Ms. Lan Anh",
            "password": "123",
            "phone": "0944555666",
        },
        "jobs": [
            {
                "title": "Nhân viên Tư vấn Tuyển sinh",
                "salary_min": 8000000,
                "salary_max": 15000000,
                "location": "Hà Nội",
                "level": "Junior",
                "description": "Tư vấn khóa học cho học viên qua điện thoại và trực tiếp.",
                "requirements": "Giọng nói chuẩn, không yêu cầu kinh nghiệm, sẽ được đào tạo.",
                "benefits": "Thưởng doanh số cao.",
                "min_years_experience": 0,
                "skills_required": ["Communication", "Sales", "Consulting"],
            },
            {
                "title": "Content Marketing Executive",
                "salary_min": 10000000,
                "salary_max": 18000000,
                "location": "Hà Nội",
                "level": "Mid-Level",
                "description": "Viết bài PR, quản lý Fanpage, xây dựng kịch bản Video TikTok.",
                "requirements": "Sáng tạo, bắt trend tốt. Có khả năng viết lách.",
                "benefits": "Du lịch công ty 2 lần/năm.",
                "min_years_experience": 1,
                "skills_required": ["Content Writing", "Social Media", "Marketing"],
            }
        ],
    },
    {
        "company": {
            "name": "Mekong Logistics",
            "industry": "Logistics & Supply Chain",
            "address": "Quận Ninh Kiều, Cần Thơ",
            "website": "https://mekonglog.example.com",
            "description": "Dịch vụ vận chuyển và kho bãi khu vực ĐBSCL.",
            "tax_number": "1801122334",
            "logo_url": "company_default.png",
        },
        "hr": {
            "email": "tuyendung@mekonglog.com",
            "full_name": "HR Mekong",
            "password": "123",
            "phone": "0939123123",
        },
        "jobs": [
            {
                "title": "Operations Supervisor",
                "salary_min": 15000000,
                "salary_max": 22000000,
                "location": "Cần Thơ",
                "level": "Team Lead",
                "description": "Giám sát vận hành kho bãi, điều phối đội xe giao hàng.",
                "requirements": "Có kinh nghiệm quản lý kho, chịu khó đi công tác.",
                "benefits": "Phụ cấp xăng xe, điện thoại.",
                "min_years_experience": 3,
                "skills_required": ["Logistics", "Management", "Operations"],
            }
        ],
    },
    {
        "company": {
            "name": "HealthCare Plus",
            "industry": "Healthcare",
            "address": "Quận 3, TP. Hồ Chí Minh",
            "website": "https://hcplus.example.com",
            "description": "Chuỗi phòng khám đa khoa quốc tế.",
            "tax_number": "0304445556",
            "logo_url": "company_default.png",
        },
        "hr": {
            "email": "hr@hcplus.com",
            "full_name": "Dr. Minh HR",
            "password": "123",
            "phone": "0909888999",
        },
        "jobs": [
            {
                "title": "Flutter Mobile Developer",
                "salary_min": 20000000,
                "salary_max": 35000000,
                "location": "Hồ Chí Minh",
                "level": "Mid-Level",
                "description": "Phát triển ứng dụng đặt lịch khám bệnh cho bệnh nhân (iOS/Android).",
                "requirements": "Thành thạo Dart/Flutter. Có kinh nghiệm publish app lên Store.",
                "benefits": "Khám sức khỏe miễn phí cho người thân.",
                "min_years_experience": 2,
                "skills_required": ["Flutter", "Dart", "Mobile Dev", "API Integration"],
            }
        ],
    },
    {
        "company": {
            "name": "Future Motors Vietnam",
            "industry": "Automotive & Manufacturing",
            "address": "Khu Kinh tế Đình Vũ - Cát Hải, Hải Phòng",
            "website": "https://futuremotors.example.com",
            "description": "Nhà sản xuất ô tô điện thông minh hàng đầu Đông Nam Á.",
            "tax_number": "0201122334",
            "logo_url": "company_default.png",
        },
        "hr": {
            "email": "tuyendung@futuremotors.com",
            "full_name": "Trần Quang Huy (HR Manufacturing)",
            "password": "123",
            "phone": "0915111222",
        },
        "jobs": [
            {
                "title": "Embedded Software Engineer (C/C++)",
                "salary_min": 25000000,
                "salary_max": 45000000,
                "location": "Hải Phòng",
                "level": "Senior",
                "description": "Phát triển phần mềm nhúng cho hệ thống điều khiển xe điện (ECU, BMS).",
                "requirements": "Thành thạo C/C++. Hiểu biết về RTOS, CAN, LIN.",
                "benefits": "Xe đưa đón Hà Nội - Hải Phòng, Ký túc xá 5 sao.",
                "min_years_experience": 3,
                "skills_required": ["C++", "Embedded Systems", "Automotive", "RTOS"],
            },
            {
                "title": "Production Supervisor (Giám sát sản xuất)",
                "salary_min": 18000000,
                "salary_max": 25000000,
                "location": "Hải Phòng",
                "level": "Team Lead",
                "description": "Giám sát dây chuyền lắp ráp, đảm bảo tiến độ và chất lượng đầu ra.",
                "requirements": "Tốt nghiệp ĐH Kỹ thuật. Có kinh nghiệm quản lý sản xuất theo mô hình Lean/Kaizen.",
                "benefits": "Thưởng năng suất, phụ cấp độc hại.",
                "min_years_experience": 2,
                "skills_required": ["Manufacturing", "Production Planning", "Kaizen", "Leadership"],
            }
        ],
    },

    # 8. TRUYỀN THÔNG & GIẢI TRÍ (MEDIA)
    {
        "company": {
            "name": "Galaxy Creative Hub",
            "industry": "Media & Advertising",
            "address": "Quận 3, TP. Hồ Chí Minh",
            "website": "https://galaxyhub.example.com",
            "description": "Production House chuyên sản xuất TVC, MV và Viral Video.",
            "tax_number": "0308889991",
            "logo_url": "company_default.png",
        },
        "hr": {
            "email": "hr@galaxyhub.com",
            "full_name": "Nguyễn Lan Phương",
            "password": "123",
            "phone": "0909333444",
        },
        "jobs": [
            {
                "title": "Video Editor / Motion Graphic",
                "salary_min": 12000000,
                "salary_max": 20000000,
                "location": "Hồ Chí Minh",
                "level": "Mid-Level",
                "description": "Dựng phim TVC quảng cáo, làm hiệu ứng 2D/3D Motion.",
                "requirements": "Thành thạo Adobe Premiere, After Effects. Có gu thẩm mỹ tốt.",
                "benefits": "Môi trường sáng tạo, thoải mái về giờ giấc.",
                "min_years_experience": 1,
                "skills_required": ["Video Editing", "After Effects", "Premiere", "Graphic Design"],
            },
            {
                "title": "Account Executive (Agency)",
                "salary_min": 10000000,
                "salary_max": 18000000,
                "location": "Hồ Chí Minh",
                "level": "Junior",
                "description": "Làm việc với khách hàng, nhận brief và quản lý tiến độ dự án quảng cáo.",
                "requirements": "Giao tiếp tốt, chịu được áp lực deadline. Tiếng Anh khá.",
                "benefits": "Thưởng dự án hấp dẫn.",
                "min_years_experience": 1,
                "skills_required": ["Account Management", "Communication", "Marketing", "English"],
            }
        ],
    },

    # 9. Y TẾ & DƯỢC PHẨM (HEALTHCARE)
    {
        "company": {
            "name": "Tam Duc Healthcare",
            "industry": "Healthcare & Pharma",
            "address": "Quận 7, TP. Hồ Chí Minh",
            "website": "https://tamduc.example.com",
            "description": "Hệ thống phòng khám đa khoa và nhà thuốc đạt chuẩn GPP.",
            "tax_number": "0307776665",
            "logo_url": "company_default.png",
        },
        "hr": {
            "email": "tuyendung@tamduc.com",
            "full_name": "Dr. Minh (Giám đốc Nhân sự)",
            "password": "123",
            "phone": "0988666777",
        },
        "jobs": [
            {
                "title": "Dược sĩ Tư vấn (Pharmacist)",
                "salary_min": 9000000,
                "salary_max": 14000000,
                "location": "Hồ Chí Minh",
                "level": "Junior",
                "description": "Tư vấn và bán thuốc theo đơn tại hệ thống nhà thuốc.",
                "requirements": "Tốt nghiệp Cao đẳng/Đại học Dược. Trung thực, cẩn thận.",
                "benefits": "Thưởng doanh số bán hàng.",
                "min_years_experience": 0,
                "skills_required": ["Pharmacy", "Consulting", "Customer Service"],
            },
            {
                "title": "Chuyên viên Kinh doanh Thiết bị Y tế",
                "salary_min": 15000000,
                "salary_max": 30000000,
                "location": "Hồ Chí Minh",
                "level": "Mid-Level",
                "description": "Giới thiệu máy móc, thiết bị y tế vào các bệnh viện lớn.",
                "requirements": "Có kinh nghiệm sales kênh ETC/Bệnh viện.",
                "benefits": "Hoa hồng cao trên hợp đồng.",
                "min_years_experience": 2,
                "skills_required": ["Sales B2B", "Medical Devices", "Negotiation"],
            }
        ],
    },

    # 10. FMCG (HÀNG TIÊU DÙNG NHANH)
    {
        "company": {
            "name": "SunFoods Vietnam",
            "industry": "FMCG",
            "address": "KCN Sóng Thần, Bình Dương",
            "website": "https://sunfoods.example.com",
            "description": "Tập đoàn sản xuất thực phẩm và đồ uống hàng đầu.",
            "tax_number": "3701234567",
            "logo_url": "company_default.png",
        },
        "hr": {
            "email": "hr@sunfoods.com",
            "full_name": "Lê Bích Ngọc",
            "password": "123",
            "phone": "0966888999",
        },
        "jobs": [
            {
                "title": "Brand Manager (Ngành hàng Đồ uống)",
                "salary_min": 35000000,
                "salary_max": 60000000,
                "location": "Hồ Chí Minh",
                "level": "Manager",
                "description": "Chịu trách nhiệm về hình ảnh thương hiệu, chiến lược tung sản phẩm mới.",
                "requirements": "5 năm kinh nghiệm Marketing ngành FMCG. Tư duy chiến lược.",
                "benefits": "Chế độ đãi ngộ cấp quản lý, xe đưa đón.",
                "min_years_experience": 5,
                "skills_required": ["Brand Management", "Marketing Strategy", "FMCG", "Leadership"],
            },
            {
                "title": "QC Supervisor (Giám sát Chất lượng)",
                "salary_min": 15000000,
                "salary_max": 22000000,
                "location": "Bình Dương",
                "level": "Team Lead",
                "description": "Kiểm soát chất lượng nguyên liệu đầu vào và thành phẩm.",
                "requirements": "Am hiểu ISO 22000, HACCP. Tốt nghiệp Công nghệ thực phẩm.",
                "benefits": "Cơm trưa, xe đưa đón từ TP.HCM.",
                "min_years_experience": 3,
                "skills_required": ["Quality Control", "HACCP", "Food Technology", "ISO"],
            }
        ],
    },

    # 11. DU LỊCH & KHÁCH SẠN
    {
        "company": {
            "name": "Ocean Blue Resort",
            "industry": "Hospitality & Tourism",
            "address": "Đường Võ Nguyên Giáp, Đà Nẵng",
            "website": "https://oceanblue.example.com",
            "description": "Khu nghỉ dưỡng 5 sao tiêu chuẩn quốc tế ven biển Mỹ Khê.",
            "tax_number": "0409998887",
            "logo_url": "company_default.png",
        },
        "hr": {
            "email": "hr@oceanblue.com",
            "full_name": "Phan Anh Tuấn (HR Manager)",
            "password": "123",
            "phone": "0905777888",
        },
        "jobs": [
            {
                "title": "Front Office Manager (Trưởng bộ phận Tiền sảnh)",
                "salary_min": 25000000,
                "salary_max": 40000000,
                "location": "Đà Nẵng",
                "level": "Manager",
                "description": "Quản lý toàn bộ hoạt động lễ tân, CSKH. Đảm bảo trải nghiệm khách hàng.",
                "requirements": "Tiếng Anh lưu loát. 3 năm kinh nghiệm quản lý khách sạn 4-5 sao.",
                "benefits": "Service Charge cao, bao ăn ở.",
                "min_years_experience": 3,
                "skills_required": ["Hotel Management", "English", "Customer Service", "Leadership"],
            },
            {
                "title": "Sales Manager (Khách đoàn/TA)",
                "salary_min": 20000000,
                "salary_max": 35000000,
                "location": "Đà Nẵng",
                "level": "Manager",
                "description": "Tìm kiếm khách hàng doanh nghiệp, công ty du lịch lữ hành.",
                "requirements": "Có network rộng với các Travel Agency.",
                "benefits": "Thưởng doanh số.",
                "min_years_experience": 3,
                "skills_required": ["Sales", "Tourism", "Networking", "Negotiation"],
            }
        ],
    }
]


def seed_data():
    with app.app_context():
        print("🚀 Bắt đầu khởi tạo dữ liệu mẫu...")

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
            if not hr_user.company_id:
                hr_user.company_id = company.id
                db.session.commit()

        print("\n⏳ Đang tạo Job và gọi Google AI (Embedding)...")

        for i in range(2):
            for template in SAMPLE_JOBS:
                job_title = f"{template['title']} ({i+1})"

                if Job.query.filter_by(title=job_title).first():
                    print(f"   Skip: {job_title}")
                    continue

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
