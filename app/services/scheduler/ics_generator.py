from ics import Calendar, Event
from ics.grammar.parse import ContentLine
import os
from flask import current_app
from datetime import timedelta


class ICSGenerator:
    @staticmethod
    def create_ics_file(interview):
        """
        Tạo file .ics chuẩn.
        Xử lý thủ công: Trừ 7 tiếng để đưa về UTC chuẩn.
        """
        c = Calendar()

        # 1. Header bắt buộc
        c.extra.append(ContentLine(name="METHOD", value="PUBLISH"))
        # Đổi tên PRODID để bạn nhận biết code mới đã chạy chưa
        c.extra.append(ContentLine(name="PRODID", value="-//CVFlow-FINAL//VN"))

        e = Event()
        e.uid = f"cvflow-{interview.id}@cvflow.vn"
        e.name = f"PV: {interview.application.job.title}"

        # 2. XỬ LÝ GIỜ (QUAN TRỌNG NHẤT)
        # Database: 08:30 (Giờ VN)
        # File ICS cần: 01:30 (Giờ UTC)
        # Hành động: Trừ đi 7 tiếng thủ công

        # start_time trong DB là dạng datetime naive (không múi giờ)
        # Ta trừ thẳng 7 tiếng
        utc_start = interview.start_time - timedelta(hours=7)
        utc_end = interview.end_time - timedelta(hours=7)

        # Gán vào sự kiện
        e.begin = utc_start
        e.end = utc_end

        # 3. Thông tin khác
        loc = interview.location or "Online"
        if interview.meeting_link:
            loc += f" - Link: {interview.meeting_link}"
        e.location = loc

        e.description = f"Ứng viên {interview.application.candidate.full_name}\nLink: {interview.meeting_link or 'N/A'}"

        c.events.add(e)

        # 4. Lưu file (Thêm timestamp để tránh cache trình duyệt)
        # Dùng os.urandom để tạo tên ngẫu nhiên hẳn hoi
        import time

        filename = f"invite_{interview.id}_{int(time.time())}.ics"
        save_path = os.path.join(current_app.root_path, "static", "invites", filename)

        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "w", encoding="utf-8", newline="") as f:
            f.writelines(c.serialize_iter())

        return filename
