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


def send_rejection_email(application):
    """
    Gửi email cảm ơn khi ứng viên bị từ chối.
    Văn phong: Chân thành, khích lệ, giữ cửa cho tương lai.
    """
    candidate = application.candidate
    job = application.job

    subject = f"[CVFlow] Thư cảm ơn từ bộ phận Tuyển dụng - {job.title}"

    body_html = f"""
    <p>Thân gửi {candidate.full_name},</p>

    <p>Lời đầu tiên, thay mặt đội ngũ tuyển dụng tại <strong>{job.company.name}</strong>, tôi xin chân thành cảm ơn bạn đã dành thời gian quan tâm và ứng tuyển cho vị trí <strong>{job.title}</strong>.</p>

    <p>Chúng tôi đã dành thời gian xem xét kỹ lưỡng hồ sơ của bạn. Mặc dù chúng tôi rất ấn tượng với những kinh nghiệm mà bạn chia sẻ, nhưng ở thời điểm hiện tại, chúng tôi nhận thấy hồ sơ của bạn chưa thực sự phù hợp với những tiêu chí cụ thể mà chúng tôi đang tìm kiếm cho giai đoạn này.</p>

    <p>Đây là một quyết định khó khăn vì số lượng ứng viên tài năng rất nhiều. Chúng tôi xin phép được lưu lại hồ sơ của bạn trong hệ thống nhân tài của công ty và sẽ chủ động liên hệ lại nếu có cơ hội phù hợp hơn trong tương lai.</p>

    <p>Một lần nữa, cảm ơn bạn đã chọn {job.company.name}. Chúc bạn luôn giữ vững đam mê và sớm tìm được bến đỗ sự nghiệp ưng ý.</p>

    <p>Trân trọng,<br>
    Bộ phận Tuyển dụng {job.company.name}</p>
    """

    msg = Message(
        subject=subject,
        recipients=[candidate.email],
        html=body_html
    )

    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Lỗi gửi email từ chối: {str(e)}")
        return False


def send_offer_email(application):
    """
    Gửi email chúc mừng khi ứng viên được chuyển sang trạng thái OFFER.
    Văn phong: Chúc mừng, hào hứng, thông báo bước tiếp theo.
    """
    candidate = application.candidate
    job = application.job

    subject = f"[CVFlow] CHÚC MỪNG: Thông báo kết quả phỏng vấn - {job.title}"

    body_html = f"""
    <h3>Thân gửi {candidate.full_name},</h3>

    <p>Chúng tôi mang đến cho bạn một tin tuyệt vời!</p>

    <p>Sau quá trình phỏng vấn và đánh giá, chúng tôi rất ấn tượng với năng lực và thái độ chuyên nghiệp của bạn. Thay mặt <strong>{job.company.name}</strong>, tôi xin trân trọng thông báo bạn đã <strong>VƯỢT QUA</strong> vòng phỏng vấn cho vị trí <strong>{job.title}</strong>.</p>

    <p>Chúng tôi tin rằng bạn sẽ là một mảnh ghép hoàn hảo cho đội ngũ của chúng tôi.</p>

    <p><strong>Bước tiếp theo:</strong> Bộ phận nhân sự sẽ sớm liên hệ trực tiếp với bạn qua điện thoại (hoặc email tiếp theo) để trao đổi chi tiết về mức lương, đãi ngộ và Thư mời nhận việc (Offer Letter) chính thức.</p>

    <p>Cảm ơn bạn đã nỗ lực trong suốt quá trình vừa qua. Chúng tôi rất mong chờ được chào đón bạn!</p>

    <p>Trân trọng,<br>
    Bộ phận Tuyển dụng {job.company.name}</p>
    """

    msg = Message(
        subject=subject,
        recipients=[candidate.email],
        html=body_html
    )

    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Lỗi gửi email offer: {str(e)}")
        return False