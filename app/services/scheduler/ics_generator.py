from ics import Calendar, Event
from datetime import timedelta
import os
from flask import current_app


class ICSGenerator:
    @staticmethod
    def create_ics_file(interview):
        """
        Tạo file .ics và lưu vào thư mục static/invites
        """
        c = Calendar()
        e = Event()

        e.name = f"Phỏng vấn: {interview.application.job.title}"
        e.begin = interview.start_time
        e.duration = timedelta(
            minutes=(interview.end_time - interview.start_time).seconds / 60
        )
        e.location = interview.location
        e.description = f"""
        Cuộc phỏng vấn với {interview.application.job.company.name}.
        Vị trí: {interview.application.job.title}
        Link họp (nếu có): {interview.meeting_link or 'N/A'}
        """

        c.events.add(e)

        # Tạo tên file unique
        filename = f"invite_{interview.id}_{int(interview.start_time.timestamp())}.ics"
        save_path = os.path.join(current_app.root_path, "static", "invites", filename)

        # Đảm bảo thư mục tồn tại
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "w", encoding="utf-8") as f:
            f.writelines(c.serialize_iter())

        return filename
