# app/services/email_service.py
from flask_mail import Message
from flask import current_app, render_template_string
from app.extensions import mail
import os


def send_interview_invitation(application, interview):
    """
    Gửi email mời phỏng vấn kèm file ICS
    """
    candidate = application.candidate
    job = application.job

    subject = f"[CVFlow] Thư mời phỏng vấn - {job.title} - {candidate.full_name}"

    # Nội dung email (Có thể chuyển sang file template HTML riêng nếu muốn đẹp hơn)
    body_html = f"""
    <h3>Xin chào {candidate.full_name},</h3>
    <p>Chúc mừng bạn! Hồ sơ ứng tuyển vị trí <strong>{job.title}</strong> của bạn đã gây ấn tượng với chúng tôi.</p>
    <p>Chúng tôi trân trọng mời bạn tham gia buổi phỏng vấn với thông tin chi tiết như sau:</p>
    <ul>
        <li><strong>Thời gian:</strong> {interview.start_time.strftime('%H:%M %d/%m/%Y')}</li>
        <li><strong>Địa điểm/Link:</strong> {interview.location}</li>
        <li><strong>Thời lượng dự kiến:</strong> {int((interview.end_time - interview.start_time).total_seconds() / 60)} phút</li>
    </ul>
    <p>Vui lòng kiểm tra file lịch (.ics) đính kèm để thêm vào lịch cá nhân của bạn.</p>
    <p>Trân trọng,<br>Bộ phận Tuyển dụng</p>
    """

    msg = Message(
        subject=subject,
        recipients=[candidate.email],  # Lấy email từ bảng User
        html=body_html
    )

    # Đính kèm file ICS (Lịch)
    if interview.ics_file_url:
        try:
            # interview.ics_file_url đang lưu dạng 'invites/filename.ics' hoặc đường dẫn tương đối
            # Cần lấy đường dẫn tuyệt đối từ thư mục static
            file_path = os.path.join(current_app.root_path, 'static', interview.ics_file_url)

            with open(file_path, 'rb') as fp:
                msg.attach(
                    filename="lich_phong_van.ics",
                    content_type="text/calendar",
                    data=fp.read()
                )
        except Exception as e:
            print(f"Lỗi đính kèm file ICS: {str(e)}")

    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Lỗi gửi email: {str(e)}")
        return False