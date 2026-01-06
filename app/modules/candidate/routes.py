import time
import os
from datetime import datetime
from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    current_app,
    request,
    jsonify,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app.extensions import db
from app.modules.candidate import candidate_bp
from app.services.ai_engine.core import review_cv_content

# 👇 Đảm bảo import đúng parser cũ của bạn
from app.services.ai_engine.parser import extract_text_from_pdf
from app.services.ai_engine.gemini_client import get_text_embedding

# Import forms
from app.modules.candidate.forms import CandidateProfileForm, CVUploadForm
from app.models.application import CV_File, Application
from app.models.scheduler import Interview
from app.services.cv_scorer import CVScorer


@candidate_bp.before_request
def check_candidate_role():
    if not current_user.is_authenticated or current_user.role != "CANDIDATE":
        flash("Trang này chỉ dành cho Ứng viên.", "warning")
        return redirect(url_for("auth.login"))


# ... (Route dashboard, profile giữ nguyên) ...


@candidate_bp.route("/dashboard")
def dashboard():
    # (Giữ nguyên code cũ của bạn)
    applied_count = Application.query.filter_by(user_id=current_user.id).count()
    interested_count = Application.query.filter(
        Application.user_id == current_user.id, Application.status != "NEW"
    ).count()
    upcoming_interviews = (
        Interview.query.join(Application)
        .filter(
            Application.user_id == current_user.id,
            Interview.start_time > datetime.utcnow(),
        )
        .order_by(Interview.start_time.asc())
        .all()
    )
    recent_activities = (
        Application.query.filter_by(user_id=current_user.id)
        .order_by(Application.created_at.desc())
        .limit(5)
        .all()
    )
    return render_template(
        "candidate/dashboard.html",
        applied_count=applied_count,
        interested_count=interested_count,
        interview_count=len(upcoming_interviews),
        upcoming_interviews=upcoming_interviews,
        recent_activities=recent_activities,
    )


@candidate_bp.route("/profile", methods=["GET", "POST"])
def profile():

    form = CandidateProfileForm()
    if request.method == "GET":
        form.phone.data = current_user.phone if current_user.phone else ""
        form.bio.data = current_user.bio if current_user.bio else ""
        if current_user.available_days:
            form.available_days.data = current_user.available_days.split(",")
        form.start_time.data = current_user.start_time
        form.end_time.data = current_user.end_time

    if form.validate_on_submit():
        current_user.phone = form.phone.data
        current_user.bio = form.bio.data
        if form.available_days.data:
            current_user.available_days = ",".join(form.available_days.data)
        else:
            current_user.available_days = ""
        current_user.start_time = form.start_time.data
        current_user.end_time = form.end_time.data
        try:
            db.session.commit()
            flash("Cập nhật hồ sơ thành công!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi khi lưu dữ liệu: {str(e)}", "danger")
        return redirect(url_for("candidate.profile"))
    return render_template("candidate/profile.html", form=form)


# 👇 ROUTE QUAN TRỌNG ĐÃ ĐƯỢC CẬP NHẬT 👇
@candidate_bp.route("/cv", methods=["GET", "POST"])
def cv_manager():
    form = CVUploadForm()

    if form.validate_on_submit():
        f = form.cv_file.data
        filename = secure_filename(f.filename)

        # Tạo tên file duy nhất
        timestamp = int(time.time())
        unique_filename = f"{current_user.id}_{timestamp}_{filename}"

        if not os.path.exists(current_app.config["UPLOAD_FOLDER"]):
            os.makedirs(current_app.config["UPLOAD_FOLDER"])

        file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)

        try:
            f.save(file_path)

            # --- 👇 BẮT ĐẦU ĐOẠN CODE MỚI: TRÍCH XUẤT TEXT ---
            print(f"📄 Đang xử lý file: {filename}")
            extracted_text = ""

            # Chỉ parse text nếu là file PDF (theo hàm parser cũ của bạn)
            if filename.lower().endswith(".pdf"):
                try:
                    extracted_text = extract_text_from_pdf(file_path) or ""
                    print(
                        f"✅ Parser PDF thành công. Độ dài text: {len(extracted_text)}"
                    )
                except Exception as p_err:
                    print(f"❌ Lỗi Parser PDF: {p_err}")
            else:
                print("⚠️ File không phải PDF, bỏ qua bước trích xuất text.")
            # --------------------------------------------------

            new_cv = CV_File(
                user_id=current_user.id,
                file_url=unique_filename,
                file_name=filename,
                # 👇 LƯU TEXT VÀO DB ĐỂ AI DÙNG SAU NÀY
                raw_text=extracted_text,
                is_main=False,
            )
            db.session.add(new_cv)
            db.session.commit()
            flash("Tải CV lên thành công!", "success")
        except Exception as e:
            flash(f"Lỗi khi lưu file: {str(e)}", "danger")

        return redirect(url_for("candidate.cv_manager"))

    cvs = (
        CV_File.query.filter_by(user_id=current_user.id)
        .order_by(CV_File.created_at.desc())
        .all()
    )
    return render_template("candidate/cv_manager.html", form=form, cvs=cvs)


@candidate_bp.route("/cv/set-main/<int:cv_id>")
def set_main_cv(cv_id):
    # Reset tất cả về False
    CV_File.query.filter_by(user_id=current_user.id).update({"is_main": False})

    # 2. Lấy CV được chọn
    target_cv = CV_File.query.get_or_404(cv_id)
    target_cv.is_main = True

    # 3. TẠO VECTOR NẾU CHƯA CÓ (Lazy Loading)
    if not target_cv.vector_embedding and target_cv.raw_text:
        print("⚡ Đang tạo Vector Embedding cho CV...")
        target_cv.vector_embedding = get_text_embedding(target_cv.raw_text)

    db.session.commit()
    flash("Đã cập nhật CV chính & đồng bộ dữ liệu AI.", "success")
    return redirect(url_for("candidate.cv_manager"))


@candidate_bp.route("/jobs")
def job_manager():
    applications = Application.query.filter_by(user_id=current_user.id).all()
    return render_template("candidate/job_manager.html", applications=applications)


@candidate_bp.route("/interviews")
def interview_list():
    interviews = (
        Interview.query.join(Application)
        .filter(Application.user_id == current_user.id)
        .order_by(Interview.start_time.desc())
        .all()
    )
    return render_template("candidate/interview_list.html", interviews=interviews)


@candidate_bp.route("/cv-manager/review/<int:cv_id>", methods=["POST"])
@login_required
def ai_review_cv(cv_id):
    # 1. KIỂM TRA QUYỀN TRUY CẬP
    cv = CV_File.query.get_or_404(cv_id)
    if cv.user_id != current_user.id:
        return (
            jsonify(
                {"success": False, "message": "Bạn không có quyền truy cập CV này"}
            ),
            403,
        )

    try:
        # 2. XỬ LÝ TEXT (Nếu chưa có thì extract lại)
        cv_text = cv.raw_text
        if not cv_text:
            file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], cv.file_url)
            if not os.path.exists(file_path):
                return (
                    jsonify({"success": False, "message": "File gốc không tồn tại"}),
                    404,
                )

            print(f"📄 [Review] Đang trích xuất text từ file: {cv.file_name}")
            cv_text = extract_text_from_pdf(file_path)

            if cv_text:
                cv.raw_text = cv_text
                db.session.commit()
            else:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "Không thể đọc nội dung text từ file PDF",
                        }
                    ),
                    400,
                )

        # --- BẮT ĐẦU LOGIC MỚI ---

        # 3. PHẦN 1: CHẤM ĐIỂM "CỨNG" (ATS SCORE) - Logic Python thuần
        # Phần này đảm bảo điểm số luôn nhất quán, không phụ thuộc AI
        print(f"🧮 [Review] Đang tính điểm chuẩn ATS cho CV ID: {cv_id}")
        scorer = CVScorer()
        ats_score, ats_details = scorer.evaluate(cv_text)

        # 4. PHẦN 2: NHẬN XÉT "MỀM" (AI REVIEW) - Dùng Gemini
        # Phần này chỉ lấy lời khuyên, không lấy điểm số
        print("🤖 [Review] Đang gửi yêu cầu nhận xét tới AI...")
        ai_result = review_cv_content(cv_text)

        if "error" in ai_result:
            # Nếu AI lỗi, vẫn trả về điểm ATS nhưng báo lỗi phần nhận xét
            print(f"⚠️ [Review] AI Error: {ai_result['error']}")
            ai_result = {
                "summary": "Hệ thống AI đang bận, chỉ có thể chấm điểm chuẩn ATS.",
                "strengths": [],
                "weaknesses": [],
                "improvements": [],
            }

        # 5. GỘP DỮ LIỆU (MERGE)
        # Cấu trúc JSON mới để lưu vào DB và trả về Frontend
        final_result = {
            "score": ats_score,  # Điểm số uy tín (từ 0-100)
            "checklist": ats_details,  # Mảng các tiêu chí đạt/không đạt (VD: ["✅ Có Email", "❌ Thiếu kỹ năng"])
            "ai_review": ai_result,  # Nội dung nhận xét chi tiết từ AI
        }

        # 6. LƯU VÀO DATABASE
        cv.ai_score = ats_score  # Lưu điểm số cứng
        cv.ai_matching_data = final_result  # Lưu trọn bộ dữ liệu phân tích
        db.session.commit()

        print(f"✅ [Review] Hoàn tất! Điểm: {ats_score}/100")

        return jsonify(
            {"success": True, "message": "Đã phân tích xong CV!", "data": final_result}
        )

    except Exception as e:
        print(f"❌ System Error [Review CV]: {e}")
        db.session.rollback()
        return jsonify({"success": False, "message": f"Lỗi hệ thống: {str(e)}"}), 500
