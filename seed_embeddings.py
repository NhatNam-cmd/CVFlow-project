import time
import os
from app import create_app, db
from app.models import Job, CV_File
from app.services.ai_engine.gemini_client import get_text_embedding
from app.services.ai_engine.parser import extract_text_from_pdf

# Khởi tạo Flask App Context để truy cập Database
app = create_app()


def seed_vectors():
    print("🚀 Bắt đầu quá trình tạo Vector Embedding cho dữ liệu cũ...")

    with app.app_context():
        # ==========================================
        # 1. XỬ LÝ JOBS (CÔNG VIỆC)
        # ==========================================
        jobs = Job.query.filter(Job.vector_embedding is None).all()
        print(f"\n📂 Tìm thấy {len(jobs)} công việc chưa có Vector.")

        for job in jobs:
            try:
                print(f"   Generating Job ID {job.id}: {job.title}...", end=" ")

                # Kết hợp nội dung để AI hiểu ngữ cảnh tốt nhất
                full_text = f"{job.title}. {job.description}. {job.requirements}"

                # Gọi API Embedding
                vector = get_text_embedding(full_text)

                if vector:
                    job.vector_embedding = vector
                    print("✅ OK")
                else:
                    print("❌ Failed (API Error)")

                # Ngủ 1 xíu để tránh spam API quá nhanh (Rate Limit)
                time.sleep(0.5)

            except Exception as e:
                print(f"❌ Lỗi: {str(e)}")

        # Lưu Job vào DB sau mỗi đợt quét
        db.session.commit()

        # ==========================================
        # 2. XỬ LÝ CV (HỒ SƠ ỨNG VIÊN)
        # ==========================================
        cvs = CV_File.query.filter(CV_File.vector_embedding is None).all()
        print(f"\n📄 Tìm thấy {len(cvs)} CV chưa có Vector.")

        for cv in cvs:
            try:
                print(f"   Generating CV ID {cv.id}: {cv.file_name}...", end=" ")

                # Kiểm tra xem đã có text chưa
                cv_text = cv.raw_text

                # Nếu chưa có text trong DB -> Phải đọc lại từ file PDF gốc
                if not cv_text:
                    file_path = os.path.join(app.config["UPLOAD_FOLDER"], cv.file_url)
                    if os.path.exists(file_path):
                        cv_text = extract_text_from_pdf(file_path)
                        cv.raw_text = cv_text  # Lưu luôn text vào DB để lần sau dùng
                    else:
                        print("⚠️ File Not Found -> Skip")
                        continue

                if not cv_text:
                    print("⚠️ Empty Text -> Skip")
                    continue

                # Gọi API Embedding
                vector = get_text_embedding(cv_text)

                if vector:
                    cv.vector_embedding = vector
                    print("✅ OK")
                else:
                    print("❌ Failed")

                time.sleep(0.5)

            except Exception as e:
                print(f"❌ Lỗi: {str(e)}")

        # Lưu CV vào DB
        db.session.commit()
        print(
            "\n🎉 HOÀN TẤT! Toàn bộ dữ liệu đã được 'thông não' với Vector Embedding."
        )


if __name__ == "__main__":
    seed_vectors()
