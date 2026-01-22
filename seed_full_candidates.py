import os
import time
from datetime import datetime
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.application import CV_File
from app.services.pdf_generator import PDFGenerator

# --- DỮ LIỆU MẪU (USER + CV DATA) ---
full_profiles = [
    {
        "account": {
            "email": "dev.senior@test.com",
            "full_name": "Nguyễn Văn A",  # Đổi key từ username -> full_name cho khớp
            "password": "123456",
            "phone": "0909123456",
            "bio": "Senior Developer yêu thích Python"
        },
        "cv_data": {
            "personal": {
                "full_name": "Nguyễn Văn A",
                "job_title": "Senior Python Developer",
                "email": "dev.senior@test.com",
                "phone": "0909 123 456",
                "address": "TP. Hồ Chí Minh",
                "linkedin": "linkedin.com/in/nguyenvana",
                "summary": "5 năm kinh nghiệm Backend với Python/Django/Flask. Chuyên sâu về Microservices."
            },
            "skills": {
                "hard_skills": ["Python", "Flask", "Django", "PostgreSQL", "Docker", "AWS"],
                "soft_skills": ["Làm việc nhóm", "Review Code", "Scrum"]
            },
            "experience": [
                {
                    "position": "Senior Backend",
                    "company": "Tech Corp",
                    "time": "2020 - Nay",
                    "description": "Xây dựng hệ thống chịu tải cao, tối ưu Database."
                }
            ],
            "education": [{"school": "Đại học Bách Khoa", "degree": "Kỹ sư IT", "time": "2015-2019"}]
        }
    },
    {
        "account": {
            "email": "mkt.lead@test.com",
            "full_name": "Trần Thị B",
            "password": "123",
            "phone": "0912345678",
            "bio": "Marketing Specialist năng động"
        },
        "cv_data": {
            "personal": {
                "full_name": "Trần Thị B",
                "job_title": "Digital Marketing Lead",
                "email": "mkt.lead@test.com",
                "phone": "0912 345 678",
                "address": "Hà Nội",
                "linkedin": "linkedin.com/in/tranthib",
                "summary": "Chuyên gia Digital Marketing với thế mạnh về Performance Marketing và SEO."
            },
            "skills": {
                "hard_skills": ["Google Ads", "Facebook Ads", "SEO", "Content Strategy"],
                "soft_skills": ["Giao tiếp", "Quản lý team"]
            },
            "experience": [
                {
                    "position": "Marketing Lead",
                    "company": "E-com Startup",
                    "time": "2021 - Nay",
                    "description": "Quản lý ngân sách 500tr/tháng, ROAS 4.0."
                }
            ],
            "education": [{"school": "Đại học Kinh Tế", "degree": "Cử nhân Marketing", "time": "2016-2020"}]
        }
    },
    {
        "account": {
            "email": "fresher.ba@test.com",
            "full_name": "Lê Văn C",
            "password": "123",
            "phone": "0888999000",
            "bio": "Fresher Business Analyst ham học hỏi"
        },
        "cv_data": {
            "personal": {
                "full_name": "Lê Văn C",
                "job_title": "Fresher Business Analyst",
                "email": "fresher.ba@test.com",
                "phone": "0888 999 000",
                "address": "Đà Nẵng",
                "linkedin": "",
                "summary": "Sinh viên mới ra trường, nắm vững quy trình phần mềm và kỹ năng phân tích nghiệp vụ."
            },
            "skills": {
                "hard_skills": ["SQL Basic", "UML", "BPMN", "Figma"],
                "soft_skills": ["Tư duy logic", "Tiếng Anh"]
            },
            "experience": [
                {
                    "position": "Intern BA",
                    "company": "FPT Software",
                    "time": "06/2023 - 09/2023",
                    "description": "Hỗ trợ viết tài liệu SRS, vẽ Mockup."
                }
            ],
            "education": [{"school": "Đại học FPT", "degree": "Cử nhân IT", "time": "2019-2023"}]
        }
    }
]


def generate_raw_text(data):
    """Tạo text thô từ JSON để lưu vào DB (giúp AI đọc được ngay)"""
    text = f"FULL NAME: {data['personal'].get('full_name')}\n"
    text += f"JOB TITLE: {data['personal'].get('job_title')}\n"
    text += f"SUMMARY: {data['personal'].get('summary')}\n"
    text += f"SKILLS: {', '.join(data['skills'].get('hard_skills', []))}\n"
    for exp in data['experience']:
        text += f"EXPERIENCE: {exp.get('position')} at {exp.get('company')} - {exp.get('description')}\n"
    return text


def run_seed():
    app = create_app()
    with app.app_context():
        print("🚀 Bắt đầu tạo dữ liệu mẫu (Accounts + CVs)...")

        upload_folder = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        for profile in full_profiles:
            acc = profile['account']
            cv_data = profile['cv_data']

            # 1. TẠO USER (Nếu chưa có)
            user = User.query.filter_by(email=acc['email']).first()
            if not user:
                # SỬA: Dùng full_name thay vì username
                # SỬA: Gán password trực tiếp để trigger setter của Model (sử dụng bcrypt của app)
                user = User(
                    full_name=acc['full_name'],
                    email=acc['email'],
                    role="CANDIDATE",
                    phone=acc['phone'],
                    bio=acc['bio'],
                    created_at=datetime.utcnow()
                )
                user.password = acc['password']  # Dòng này sẽ gọi setter trong models/user.py để hash pass

                db.session.add(user)
                db.session.commit()  # Commit user để lấy ID cho bước sau
                print(f"✅ Đã tạo User: {acc['email']} (Pass: {acc['password']})")
            else:
                print(f"ℹ️ User {acc['email']} đã tồn tại. Bỏ qua bước tạo user.")

            # 2. TẠO FILE PDF
            timestamp = int(time.time())
            filename = f"seed_{user.id}_{timestamp}.pdf"
            file_path = os.path.join(upload_folder, filename)

            try:
                PDFGenerator.create_cv_pdf(cv_data, file_path)
            except Exception as e:
                print(f"❌ Lỗi tạo PDF cho {acc['email']}: {e}")
                continue

            # 3. TẠO CV TRONG DATABASE
            existing_cv = CV_File.query.filter_by(user_id=user.id, cv_source="BUILDER").first()

            if not existing_cv:
                new_cv = CV_File(
                    user_id=user.id,
                    file_url=filename,
                    file_name=f"CV {cv_data['personal']['job_title']}",
                    cv_source="BUILDER",
                    structured_data=cv_data,
                    raw_text=generate_raw_text(cv_data),
                    is_main=True,
                    created_at=datetime.utcnow()
                )
                db.session.add(new_cv)
                print(f"   📄 Đã tạo CV & PDF cho {acc['email']}")
            else:
                print(f"   ℹ️ User này đã có CV mẫu.")

        db.session.commit()
        print("\n🎉 Hoàn tất! Danh sách tài khoản test:")
        for p in full_profiles:
            print(f"- Email: {p['account']['email']} | Pass: {p['account']['password']}")


if __name__ == "__main__":
    run_seed()