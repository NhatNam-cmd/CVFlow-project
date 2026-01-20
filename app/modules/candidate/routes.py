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
from app.services.pdf_generator import PDFGenerator
from flask import send_file
from app.services.ai_engine.parser import extract_text_from_pdf
from app.services.ai_engine.gemini_client import get_text_embedding
from app.services.ai_engine.recommender import recommend_jobs_for_cv

from app.modules.candidate.forms import CandidateProfileForm, CVUploadForm
from app.models.application import CV_File, Application
from app.models.scheduler import Interview
from app.services.cv_scorer import CVScorer


@candidate_bp.before_request
def check_candidate_role():
    if not current_user.is_authenticated or current_user.role != "CANDIDATE":
        flash("Trang này chỉ dành cho Ứng viên.", "warning")
        return redirect(url_for("auth.login"))


@candidate_bp.route("/dashboard")
def dashboard():
    # 1. Các thống kê cũ (Giữ nguyên)
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

    # 2. PHẦN GỢI Ý JOB (Sửa ở đây)
    suggested_jobs = []

    # 👇 CHÚ Ý: Phải dùng .first()
    main_cv = CV_File.query.filter_by(user_id=current_user.id, is_main=True).first()

    if main_cv:
        # Giờ main_cv là object, hàm này mới chạy được
        suggested_jobs = recommend_jobs_for_cv(main_cv, top_n=6)

    return render_template(
        "candidate/dashboard.html",
        applied_count=applied_count,
        interested_count=interested_count,
        interview_count=len(upcoming_interviews),
        upcoming_interviews=upcoming_interviews,
        recent_activities=recent_activities,
        suggested_jobs=suggested_jobs,
        main_cv=main_cv,
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


@candidate_bp.route("/cv", methods=["GET", "POST"])
def cv_manager():
    form = CVUploadForm()

    if form.validate_on_submit():
        f = form.cv_file.data
        filename = secure_filename(f.filename)

        timestamp = int(time.time())
        unique_filename = f"{current_user.id}_{timestamp}_{filename}"

        if not os.path.exists(current_app.config["UPLOAD_FOLDER"]):
            os.makedirs(current_app.config["UPLOAD_FOLDER"])

        file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)

        try:
            f.save(file_path)

            print(f"📄 Đang xử lý file: {filename}")
            extracted_text = ""

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
    cv = CV_File.query.get_or_404(cv_id)
    if cv.user_id != current_user.id:
        return (
            jsonify(
                {"success": False, "message": "Bạn không có quyền truy cập CV này"}
            ),
            403,
        )

    try:
        cv_text = ""
        source_type = ""

        if cv.cv_source == "BUILDER":
            cv_text = cv.raw_text
            source_type = "CV Builder (Dữ liệu có cấu trúc)"

        else:
            source_type = "File Upload (PDF Parsing)"

            if not cv.raw_text:
                file_path = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], cv.file_url
                )
                if not os.path.exists(file_path):
                    return (
                        jsonify(
                            {"success": False, "message": "File gốc không tồn tại"}
                        ),
                        404,
                    )

                print(f"📄 [Review] Đang trích xuất text từ file PDF: {cv.file_name}")
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
            else:
                cv_text = cv.raw_text

        print(f"🧮 [Review] Đang tính điểm chuẩn ATS cho CV ID: {cv_id}")
        scorer = CVScorer()
        ats_score, ats_details = scorer.evaluate(cv)

        print("🤖 [Review] Đang gửi yêu cầu nhận xét tới AI...")
        ai_result = review_cv_content(cv_text, source_type=source_type)

        if "error" in ai_result:
            print(f"⚠️ [Review] AI Error: {ai_result['error']}")
            ai_result = {
                "summary": "Hệ thống AI đang bận hoặc gặp lỗi kết nối.",
                "strengths": [],
                "weaknesses": [],
                "improvements": [],
            }

        # 5. TỔNG HỢP VÀ LƯU KẾT QUẢ
        final_result = {
            "score": ats_score,
            "checklist": ats_details,
            "ai_review": ai_result,
        }

        cv.ai_score = ats_score
        cv.ai_matching_data = final_result
        db.session.commit()

        print(f"✅ [Review] Hoàn tất! Điểm: {ats_score}/100")

        return jsonify(
            {"success": True, "message": "Đã phân tích xong CV!", "data": final_result}
        )

    except Exception as e:
        print(f"❌ System Error [Review CV]: {e}")
        db.session.rollback()
        return jsonify({"success": False, "message": f"Lỗi hệ thống: {str(e)}"}), 500


@candidate_bp.route("/cv/builder", defaults={"cv_id": None}, methods=["GET", "POST"])
@candidate_bp.route("/cv/builder/<int:cv_id>", methods=["GET", "POST"])
@login_required
def cv_builder(cv_id):
    target_cv = None

    if cv_id:
        target_cv = CV_File.query.get_or_404(cv_id)
        if target_cv.user_id != current_user.id:
            return redirect(url_for("candidate.cv_manager"))

    if request.method == "POST":
        data = request.get_json()

        try:
            personal = data.get("personal", {})
            skills = data.get("skills", {})

            raw_text_content = f"""
            FULL NAME: {personal.get('full_name')}
            EMAIL: {personal.get('email')}
            PHONE: {personal.get('phone')}
            SUMMARY: {personal.get('summary')}

            SKILLS: {', '.join(skills.get('hard_skills', []))}
            SOFT SKILLS: {', '.join(skills.get('soft_skills', []))}

            EXPERIENCE:
            """
            for exp in data.get("experience", []):
                raw_text_content += f"\n- {exp.get('position')} at {exp.get('company')}: {exp.get('description')}"

            raw_text_content += "\n\nEDUCATION:"
            for edu in data.get("education", []):
                raw_text_content += f"\n- {edu.get('school')} ({edu.get('degree')})"

            if target_cv:
                target_cv.file_name = (
                    f"CV Online - {datetime.now().strftime('%d/%m/%Y')} (Updated)"
                )
                target_cv.structured_data = data
                target_cv.raw_text = raw_text_content

                file_path = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], target_cv.file_url
                )
                PDFGenerator.create_cv_pdf(data, file_path)

                msg = "Đã cập nhật CV thành công!"
            else:

                timestamp = int(datetime.utcnow().timestamp())
                filename = f"Digital_CV_{current_user.id}_{timestamp}.pdf"

                upload_folder = current_app.config["UPLOAD_FOLDER"]
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)

                file_path = os.path.join(upload_folder, filename)
                PDFGenerator.create_cv_pdf(data, file_path)

                target_cv = CV_File(
                    user_id=current_user.id,
                    file_name=f"CV Online - {datetime.now().strftime('%d/%m/%Y')}",
                    file_url=filename,
                    cv_source="BUILDER",
                    structured_data=data,
                    raw_text=raw_text_content,
                    created_at=datetime.utcnow(),
                )
                db.session.add(target_cv)
                msg = "Đã tạo CV mới thành công!"
            target_cv.vector_embedding = get_text_embedding(raw_text_content)

            db.session.commit()

            return jsonify({"success": True, "message": msg})

        except Exception as e:
            print(f"❌ Lỗi lưu CV Builder: {e}")
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

    return render_template("candidate/cv_builder.html", cv=target_cv)


@candidate_bp.route("/cv/delete/<int:cv_id>", methods=["POST"])
@login_required
def delete_cv(cv_id):
    cv = CV_File.query.get_or_404(cv_id)

    # Check quyền
    if cv.user_id != current_user.id:
        flash("Bạn không có quyền xóa CV này.", "danger")
        return redirect(url_for("candidate.cv_manager"))

    if cv.is_main:
        flash(
            "Không thể xóa CV đang được đặt làm Chính. Hãy chọn CV khác làm chính trước.",
            "warning",
        )
        return redirect(url_for("candidate.cv_manager"))

    try:

        if cv.file_url:
            file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], cv.file_url)
            if os.path.exists(file_path):
                os.remove(file_path)

        db.session.delete(cv)
        db.session.commit()
        flash("Đã xóa CV thành công.", "success")

    except Exception as e:
        print(f"Delete Error: {e}")
        db.session.rollback()
        flash("Lỗi khi xóa CV.", "danger")

    return redirect(url_for("candidate.cv_manager"))


@candidate_bp.route("/cv/download/<int:cv_id>")
@login_required
def download_cv_pdf(cv_id):
    cv = CV_File.query.get_or_404(cv_id)

    if cv.user_id != current_user.id:
        flash("Bạn không có quyền tải file này.", "danger")
        return redirect(url_for("candidate.cv_manager"))

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    file_path = os.path.join(upload_folder, cv.file_url)

    if (
        not os.path.exists(file_path)
        and cv.cv_source == "BUILDER"
        and cv.structured_data
    ):
        print(f"⚠️ File PDF {cv.file_url} bị thiếu. Đang tạo lại từ dữ liệu...")
        try:

            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            PDFGenerator.create_cv_pdf(cv.structured_data, file_path)
            print("✅ Đã khôi phục file PDF thành công.")
        except Exception as e:
            print(f"❌ Lỗi khôi phục PDF: {e}")
            flash("Không thể tạo file PDF. Vui lòng thử lại sau.", "danger")
            return redirect(url_for("candidate.cv_manager"))

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=cv.file_url)
    else:
        flash("File không tồn tại trên hệ thống.", "danger")
        return redirect(url_for("candidate.cv_manager"))
