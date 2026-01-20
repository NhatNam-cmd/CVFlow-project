import random
from app import create_app, db
from app.models import User, Job, CV_File, Application
from datetime import datetime, timedelta


REJECTION_REASONS = [
    ("Thiếu kinh nghiệm thực tế (Project)", 40),  # 40% bị loại vì lý do này
    ("Tiếng Anh giao tiếp yếu", 25),
    ("Deal lương quá cao so với Budget", 15),
    ("CV trình bày kém / Sai lỗi chính tả", 10),
    ("Không phù hợp văn hóa công ty", 10),
]


def get_weighted_reason():
    """Random lý do từ chối dựa trên trọng số"""
    reasons, weights = zip(*REJECTION_REASONS)
    return random.choices(reasons, weights=weights, k=1)[0]


def seed_full_market_data():
    app = create_app()
    with app.app_context():
        print("🚀 Đang khởi tạo dữ liệu Ứng tuyển & Thị trường...")

        jobs = Job.query.filter_by(is_active=True).all()
        if not jobs:
            print("❌ Chưa có Job nào. Hãy chạy seed_jobs.py trước!")
            return

        print(f"📂 Tìm thấy {len(jobs)} công việc đang mở.")

        candidates = []
        for i in range(30):
            try:
                import names

                full_name = names.get_full_name()
            except ImportError:
                full_name = f"Candidate {i+1}"

            email = f"candidate_{i+1}@test.com"

            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    full_name=full_name,
                    email=email,
                    password="password123",  # Password mặc định
                    role="CANDIDATE",
                    phone=f"090{random.randint(1000000, 9999999)}",
                )
                db.session.add(user)
                db.session.commit()  # Commit để lấy ID

                cv = CV_File(
                    user_id=user.id,
                    file_url="dummy_cv.pdf",
                    file_name=f"CV_{full_name.replace(' ', '_')}.pdf",
                    is_main=True,
                    raw_text="Kinh nghiệm làm việc: Python, Java, SQL. Dự án: E-commerce. Học vấn: ĐH Bách Khoa.",
                    ai_score=random.randint(40, 90),  # Điểm AI random
                )
                db.session.add(cv)
                db.session.commit()
                print(f"   + Đã tạo Candidate: {full_name}")

            candidates.append(user)

        print("\n⚡ Đang rải hồ sơ và chấm rớt...")

        for job in jobs:
            num_applicants = random.randint(3, 15)

            applicants = random.sample(
                candidates, k=min(num_applicants, len(candidates))
            )

            for candidate in applicants:
                exist_app = Application.query.filter_by(
                    job_id=job.id, user_id=candidate.id
                ).first()
                if exist_app:
                    continue

                cv = CV_File.query.filter_by(user_id=candidate.id).first()

                rand_status = random.random()
                status = "NEW"
                rejected_reason = None

                if rand_status < 0.6:  # 60% TỪ CHỐI
                    status = "REJECTED"
                    rejected_reason = get_weighted_reason()
                elif rand_status < 0.8:
                    status = "INTERVIEW"

                app = Application(
                    job_id=job.id,
                    user_id=candidate.id,
                    cv_id=cv.id if cv else None,
                    cover_letter="Tôi rất thích công việc này. Mong quý công ty xem xét.",
                    status=status,
                    rejected_reason=rejected_reason,
                    match_score=random.randint(50, 95),  # Fake điểm khớp
                    created_at=datetime.utcnow()
                    - timedelta(
                        days=random.randint(0, 30)
                    ),  # Random ngày nộp trong tháng qua
                )

                db.session.add(app)

        db.session.commit()
        print("\n🎉 XONG! Đã có dữ liệu 'thật' để test báo cáo.")
        print("👉 Hãy vào trang /market-report để xem biểu đồ tròn và tỷ lệ chọi mới.")


if __name__ == "__main__":
    seed_full_market_data()
