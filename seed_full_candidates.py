import os
import time
from datetime import datetime
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.application import CV_File
from app.services.pdf_generator import PDFGenerator

full_profiles = [
    {
        "account": {
            "email": "dev.senior@test.com",
            "full_name": "Nguyễn Văn A",  # Đổi key từ username -> full_name cho khớp
            "password": "123456",
            "phone": "0909123456",
            "bio": "Senior Developer yêu thích Python",
        },
        "cv_data": {
            "personal": {
                "full_name": "Nguyễn Văn A",
                "job_title": "Senior Python Developer",
                "email": "dev.senior@test.com",
                "phone": "0909 123 456",
                "address": "TP. Hồ Chí Minh",
                "linkedin": "linkedin.com/in/nguyenvana",
                "summary": "5 năm kinh nghiệm Backend với Python/Django/Flask. Chuyên sâu về Microservices.",
            },
            "skills": {
                "hard_skills": [
                    "Python",
                    "Flask",
                    "Django",
                    "PostgreSQL",
                    "Docker",
                    "AWS",
                ],
                "soft_skills": ["Làm việc nhóm", "Review Code", "Scrum"],
            },
            "experience": [
                {
                    "position": "Senior Backend",
                    "company": "Tech Corp",
                    "time": "2020 - Nay",
                    "description": "Xây dựng hệ thống chịu tải cao, tối ưu Database.",
                }
            ],
            "education": [
                {
                    "school": "Đại học Bách Khoa",
                    "degree": "Kỹ sư IT",
                    "time": "2015-2019",
                }
            ],
        },
    },
    {
        "account": {
            "email": "mkt.lead@test.com",
            "full_name": "Trần Thị B",
            "password": "123",
            "phone": "0912345678",
            "bio": "Marketing Specialist năng động",
        },
        "cv_data": {
            "personal": {
                "full_name": "Trần Thị B",
                "job_title": "Digital Marketing Lead",
                "email": "mkt.lead@test.com",
                "phone": "0912 345 678",
                "address": "Hà Nội",
                "linkedin": "linkedin.com/in/tranthib",
                "summary": "Chuyên gia Digital Marketing với thế mạnh về Performance Marketing và SEO.",
            },
            "skills": {
                "hard_skills": [
                    "Google Ads",
                    "Facebook Ads",
                    "SEO",
                    "Content Strategy",
                ],
                "soft_skills": ["Giao tiếp", "Quản lý team"],
            },
            "experience": [
                {
                    "position": "Marketing Lead",
                    "company": "E-com Startup",
                    "time": "2021 - Nay",
                    "description": "Quản lý ngân sách 500tr/tháng, ROAS 4.0.",
                }
            ],
            "education": [
                {
                    "school": "Đại học Kinh Tế",
                    "degree": "Cử nhân Marketing",
                    "time": "2016-2020",
                }
            ],
        },
    },
    {
        "account": {
            "email": "fresher.ba@test.com",
            "full_name": "Lê Văn C",
            "password": "123",
            "phone": "0888999000",
            "bio": "Fresher Business Analyst ham học hỏi",
        },
        "cv_data": {
            "personal": {
                "full_name": "Lê Văn C",
                "job_title": "Fresher Business Analyst",
                "email": "fresher.ba@test.com",
                "phone": "0888 999 000",
                "address": "Đà Nẵng",
                "linkedin": "",
                "summary": "Sinh viên mới ra trường, nắm vững quy trình phần mềm và kỹ năng phân tích nghiệp vụ.",
            },
            "skills": {
                "hard_skills": ["SQL Basic", "UML", "BPMN", "Figma"],
                "soft_skills": ["Tư duy logic", "Tiếng Anh"],
            },
            "experience": [
                {
                    "position": "Intern BA",
                    "company": "FPT Software",
                    "time": "06/2023 - 09/2023",
                    "description": "Hỗ trợ viết tài liệu SRS, vẽ Mockup.",
                }
            ],
            "education": [
                {"school": "Đại học FPT", "degree": "Cử nhân IT", "time": "2019-2023"}
            ],
        },
    },
{
        "account": {
            "email": "tung.java@test.com",
            "full_name": "Nguyễn Thanh Tùng",
            "password": "123",
            "phone": "0988111222",
            "bio": "Java Lead với 6 năm kinh nghiệm xây dựng hệ thống Fintech.",
        },
        "cv_data": {
            "personal": {
                "full_name": "Nguyễn Thanh Tùng",
                "job_title": "Senior Java Developer",
                "email": "tung.java@test.com",
                "phone": "0988 111 222",
                "address": "Cầu Giấy, Hà Nội",
                "linkedin": "linkedin.com/in/tungjava",
                "summary": "6 năm kinh nghiệm Java/Spring Boot. Chuyên sâu về Microservices và xử lý giao dịch tài chính (Core Banking).",
            },
            "skills": {
                "hard_skills": ["Java", "Spring Boot", "Microservices", "Oracle", "Kafka", "Redis"],
                "soft_skills": ["Lãnh đạo nhóm", "Giải quyết vấn đề", "Tiếng Anh (IELTS 6.5)"],
            },
            "experience": [
                {
                    "position": "Technical Lead",
                    "company": "FPT Software",
                    "time": "2021 - Nay",
                    "description": "Lead team 10 người phát triển hệ thống thanh toán cho khách hàng Nhật. Tối ưu hiệu năng DB.",
                },
                {
                    "position": "Java Developer",
                    "company": "Viettel Digital",
                    "time": "2018 - 2021",
                    "description": "Phát triển backend cho ứng dụng ViettelPay.",
                }
            ],
            "education": [
                {"school": "Đại học Bách Khoa Hà Nội", "degree": "Kỹ sư CNTT", "time": "2014-2018"}
            ],
        },
    },

    # 2. ỨNG VIÊN DATA ANALYST (Match với Job: Data Analyst - FinSmart / Risk Mgmt - VinaBank)
    {
        "account": {
            "email": "ha.data@test.com",
            "full_name": "Lê Thu Hà",
            "password": "123",
            "phone": "0912333444",
            "bio": "Data Analyst đam mê những con số.",
        },
        "cv_data": {
            "personal": {
                "full_name": "Lê Thu Hà",
                "job_title": "Data Analyst",
                "email": "ha.data@test.com",
                "phone": "0912 333 444",
                "address": "Quận 3, TP.HCM",
                "linkedin": "linkedin.com/in/lethuha",
                "summary": "Chuyên viên phân tích dữ liệu với thế mạnh về SQL, Python và trực quan hóa dữ liệu (Tableau/PowerBI). Có kinh nghiệm trong mảng Tài chính.",
            },
            "skills": {
                "hard_skills": ["Python", "SQL", "Tableau", "PowerBI", "Pandas", "Statistics"],
                "soft_skills": ["Tư duy phản biện", "Thuyết trình dữ liệu"],
            },
            "experience": [
                {
                    "position": "Data Analyst",
                    "company": "Momo E-Wallet",
                    "time": "2022 - Nay",
                    "description": "Phân tích hành vi người dùng, xây dựng Dashboard theo dõi KPI hàng ngày.",
                }
            ],
            "education": [
                {"school": "Đại học Ngoại Thương CS2", "degree": "Cử nhân Kinh tế Đối ngoại", "time": "2018-2022"}
            ],
        },
    },

    # 3. ỨNG VIÊN FRONTEND (Match với Job: ReactJS Dev - E-Shop Vietnam)
    {
        "account": {
            "email": "bao.frontend@test.com",
            "full_name": "Trần Quốc Bảo",
            "password": "123",
            "phone": "0905666777",
            "bio": "Frontend Dev yêu cái đẹp & UX.",
        },
        "cv_data": {
            "personal": {
                "full_name": "Trần Quốc Bảo",
                "job_title": "Frontend Developer",
                "email": "bao.frontend@test.com",
                "phone": "0905 666 777",
                "address": "Thủ Đức, TP.HCM",
                "linkedin": "linkedin.com/in/tqbao",
                "summary": "Lập trình viên Frontend với 3 năm kinh nghiệm ReactJS/NextJS. Có mắt thẩm mỹ tốt, kỹ tính trong từng pixel.",
            },
            "skills": {
                "hard_skills": ["JavaScript", "ReactJS", "NextJS", "HTML5/CSS3", "TailwindCSS", "Figma"],
                "soft_skills": ["Làm việc nhóm", "Quản lý thời gian"],
            },
            "experience": [
                {
                    "position": "Frontend Developer",
                    "company": "VNG Corporation",
                    "time": "2021 - Nay",
                    "description": "Phát triển giao diện web ZaloPay. Tối ưu Core Web Vitals.",
                }
            ],
            "education": [
                {"school": "Đại học CNTT - ĐHQG TP.HCM", "degree": "Kỹ sư Phần mềm", "time": "2017-2021"}
            ],
        },
    },

    # 4. ỨNG VIÊN MOBILE DEV (Match với Job: Flutter Mobile Dev - HealthCare Plus)
    {
        "account": {
            "email": "dat.mobile@test.com",
            "full_name": "Phạm Tiến Đạt",
            "password": "123",
            "phone": "0933888999",
            "bio": "Mobile Developer (iOS/Android).",
        },
        "cv_data": {
            "personal": {
                "full_name": "Phạm Tiến Đạt",
                "job_title": "Mobile App Developer",
                "email": "dat.mobile@test.com",
                "phone": "0933 888 999",
                "address": "Bình Thạnh, TP.HCM",
                "linkedin": "",
                "summary": "Thành thạo Flutter và Swift. Đã publish 5 ứng dụng lên App Store và Play Store.",
            },
            "skills": {
                "hard_skills": ["Flutter", "Dart", "Swift", "Firebase", "RESTful API"],
                "soft_skills": ["Tự học", "Kiên nhẫn"],
            },
            "experience": [
                {
                    "position": "Mobile Developer",
                    "company": "Outsourcing Company",
                    "time": "2020 - 2023",
                    "description": "Làm dự án outsourcing app đặt xe, app thương mại điện tử.",
                }
            ],
            "education": [
                {"school": "Cao đẳng FPT Polytechnic", "degree": "Lập trình di động", "time": "2018-2020"}
            ],
        },
    },

    # 5. ỨNG VIÊN EMBEDDED (Match với Job: Embedded Engineer - Future Motors)
    {
        "account": {
            "email": "nam.embedded@test.com",
            "full_name": "Hoàng Văn Nam",
            "password": "123",
            "phone": "0915555666",
            "bio": "Kỹ sư nhúng, đam mê IoT và Automotive.",
        },
        "cv_data": {
            "personal": {
                "full_name": "Hoàng Văn Nam",
                "job_title": "Embedded Software Engineer",
                "email": "nam.embedded@test.com",
                "phone": "0915 555 666",
                "address": "Hải Phòng",
                "linkedin": "",
                "summary": "Kỹ sư hệ thống nhúng với nền tảng C/C++ vững chắc. Có kinh nghiệm làm việc với vi điều khiển STM32 và RTOS.",
            },
            "skills": {
                "hard_skills": ["C/C++", "Embedded Linux", "RTOS", "STM32", "Altium Designer"],
                "soft_skills": ["Phân tích mạch", "Teamwork"],
            },
            "experience": [
                {
                    "position": "Embedded Engineer",
                    "company": "Viettel High Tech",
                    "time": "2019 - 2023",
                    "description": "Phát triển firmware cho thiết bị IoT giám sát hành trình.",
                }
            ],
            "education": [
                {"school": "Đại học Bách Khoa Hà Nội", "degree": "Kỹ thuật Điện tử Viễn thông", "time": "2015-2019"}
            ],
        },
    },

    # 6. ỨNG VIÊN SALES BĐS (Match với Job: Trưởng phòng KD BĐS - GreenLand)
    {
        "account": {
            "email": "phuc.sales@test.com",
            "full_name": "Đặng Hữu Phúc",
            "password": "123",
            "phone": "0909123123",
            "bio": "Chuyên gia bán hàng Bất động sản cao cấp.",
        },
        "cv_data": {
            "personal": {
                "full_name": "Đặng Hữu Phúc",
                "job_title": "Sales Manager",
                "email": "phuc.sales@test.com",
                "phone": "0909 123 123",
                "address": "Quận 7, TP.HCM",
                "linkedin": "",
                "summary": "5 năm kinh nghiệm trong ngành BĐS. Kỹ năng đàm phán chốt deal tốt. Đã từng quản lý nhóm 15 nhân viên.",
            },
            "skills": {
                "hard_skills": ["Sales B2C", "Bất động sản", "CRM", "Training đội ngũ"],
                "soft_skills": ["Giao tiếp", "Thuyết phục", "Chịu áp lực cao"],
            },
            "experience": [
                {
                    "position": "Team Leader",
                    "company": "Novaland Group",
                    "time": "2020 - 2023",
                    "description": "Quản lý nhóm kinh doanh dự án Aqua City. Đạt Top Sales 2021.",
                }
            ],
            "education": [
                {"school": "Đại học Kinh Tế TP.HCM", "degree": "Quản trị Kinh doanh", "time": "2014-2018"}
            ],
        },
    },

    # 7. ỨNG VIÊN MARKETING (Match với Job: Content Marketing - Green Edu / Marketing Exec - Golden Gate)
    {
        "account": {
            "email": "linh.content@test.com",
            "full_name": "Mai Thùy Linh",
            "password": "123",
            "phone": "0944567567",
            "bio": "Content Creator sáng tạo & bắt trend.",
        },
        "cv_data": {
            "personal": {
                "full_name": "Mai Thùy Linh",
                "job_title": "Content Marketing Specialist",
                "email": "linh.content@test.com",
                "phone": "0944 567 567",
                "address": "Hà Nội",
                "linkedin": "",
                "summary": "Sáng tạo nội dung đa kênh (Facebook, TikTok, Blog). Có khả năng quay dựng video cơ bản trên điện thoại.",
            },
            "skills": {
                "hard_skills": ["Copywriting", "SEO Content", "Social Media", "Canva", "CapCut"],
                "soft_skills": ["Sáng tạo", "Linh hoạt"],
            },
            "experience": [
                {
                    "position": "Content Executive",
                    "company": "Admicro Agency",
                    "time": "2022 - Nay",
                    "description": "Viết bài PR cho các nhãn hàng F&B và Giáo dục. Quản lý Fanpage.",
                }
            ],
            "education": [
                {"school": "Học viện Báo chí và Tuyên truyền", "degree": "Quan hệ Công chúng", "time": "2018-2022"}
            ],
        },
    },

    # 8. ỨNG VIÊN LOGISTICS (Match với Job: Operations Supervisor - Mekong Logistics)
    {
        "account": {
            "email": "kiet.logistics@test.com",
            "full_name": "Võ Tuấn Kiệt",
            "password": "123",
            "phone": "0939555666",
            "bio": "Chuyên viên vận hành kho vận.",
        },
        "cv_data": {
            "personal": {
                "full_name": "Võ Tuấn Kiệt",
                "job_title": "Logistics Supervisor",
                "email": "kiet.logistics@test.com",
                "phone": "0939 555 666",
                "address": "Cần Thơ",
                "linkedin": "",
                "summary": "Có kinh nghiệm quản lý kho bãi và điều phối đội xe giao hàng chặng cuối (Last-mile delivery).",
            },
            "skills": {
                "hard_skills": ["Quản lý kho (WMS)", "Excel nâng cao", "Điều phối vận tải", "SAP"],
                "soft_skills": ["Giải quyết sự cố", "Sắp xếp công việc"],
            },
            "experience": [
                {
                    "position": "Shift Leader",
                    "company": "Shopee Express",
                    "time": "2021 - 2023",
                    "description": "Giám sát ca làm việc tại kho phân loại SOC. Đảm bảo KPI về thời gian xử lý đơn hàng.",
                }
            ],
            "education": [
                {"school": "Đại học Cần Thơ", "degree": "Kinh doanh Quốc tế", "time": "2017-2021"}
            ],
        },
    },

    # 9. ỨNG VIÊN GIÁO VIÊN TIẾNG ANH (Match với Job: IELTS Teacher - EduStar)
    {
        "account": {
            "email": "an.english@test.com",
            "full_name": "Trần Bình An",
            "password": "123",
            "phone": "0905111333",
            "bio": "Giáo viên IELTS 8.0.",
        },
        "cv_data": {
            "personal": {
                "full_name": "Trần Bình An",
                "job_title": "English Teacher (IELTS)",
                "email": "an.english@test.com",
                "phone": "0905 111 333",
                "address": "Đà Nẵng",
                "linkedin": "",
                "summary": "IELTS 8.0 Overall. 3 năm kinh nghiệm giảng dạy IELTS tại các trung tâm lớn. Phong cách dạy truyền cảm hứng.",
            },
            "skills": {
                "hard_skills": ["IELTS Teaching", "Public Speaking", "Curriculum Design"],
                "soft_skills": ["Sư phạm", "Giao tiếp"],
            },
            "experience": [
                {
                    "position": "IELTS Teacher",
                    "company": "VUS",
                    "time": "2020 - 2023",
                    "description": "Dạy các lớp IELTS Foundation đến Advanced. Chấm bài Writing.",
                }
            ],
            "education": [
                {"school": "Đại học Ngoại Ngữ Đà Nẵng", "degree": "Sư phạm Tiếng Anh", "time": "2016-2020"}
            ],
        },
    }
]


def generate_raw_text(data):
    """Tạo text thô từ JSON để lưu vào DB (giúp AI đọc được ngay)"""
    text = f"FULL NAME: {data['personal'].get('full_name')}\n"
    text += f"JOB TITLE: {data['personal'].get('job_title')}\n"
    text += f"SUMMARY: {data['personal'].get('summary')}\n"
    text += f"SKILLS: {', '.join(data['skills'].get('hard_skills', []))}\n"
    for exp in data["experience"]:
        text += f"EXPERIENCE: {exp.get('position')} at {exp.get('company')} - {exp.get('description')}\n"
    return text


def run_seed():
    app = create_app()
    with app.app_context():
        print("🚀 Bắt đầu tạo dữ liệu mẫu (Accounts + CVs)...")

        upload_folder = app.config["UPLOAD_FOLDER"]
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        for profile in full_profiles:
            acc = profile["account"]
            cv_data = profile["cv_data"]

            user = User.query.filter_by(email=acc["email"]).first()
            if not user:
                user = User(
                    full_name=acc["full_name"],
                    email=acc["email"],
                    role="CANDIDATE",
                    phone=acc["phone"],
                    bio=acc["bio"],
                    created_at=datetime.utcnow(),
                )
                user.password = acc[
                    "password"
                ]  # Dòng này sẽ gọi setter trong models/user.py để hash pass

                db.session.add(user)
                db.session.commit()  # Commit user để lấy ID cho bước sau
                print(f"✅ Đã tạo User: {acc['email']} (Pass: {acc['password']})")
            else:
                print(f"ℹ️ User {acc['email']} đã tồn tại. Bỏ qua bước tạo user.")

            timestamp = int(time.time())
            filename = f"seed_{user.id}_{timestamp}.pdf"
            file_path = os.path.join(upload_folder, filename)

            try:
                PDFGenerator.create_cv_pdf(cv_data, file_path)
            except Exception as e:
                print(f"❌ Lỗi tạo PDF cho {acc['email']}: {e}")
                continue

            existing_cv = CV_File.query.filter_by(
                user_id=user.id, cv_source="BUILDER"
            ).first()

            if not existing_cv:
                new_cv = CV_File(
                    user_id=user.id,
                    file_url=filename,
                    file_name=f"CV {cv_data['personal']['job_title']}",
                    cv_source="BUILDER",
                    structured_data=cv_data,
                    raw_text=generate_raw_text(cv_data),
                    is_main=True,
                    created_at=datetime.utcnow(),
                )
                db.session.add(new_cv)
                print(f"   📄 Đã tạo CV & PDF cho {acc['email']}")
            else:
                print(f"   ℹ️ User này đã có CV mẫu.")

        db.session.commit()
        print("\n🎉 Hoàn tất! Danh sách tài khoản test:")
        for p in full_profiles:
            print(
                f"- Email: {p['account']['email']} | Pass: {p['account']['password']}"
            )


if __name__ == "__main__":
    run_seed()
