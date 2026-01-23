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

        c.extra.append(ContentLine(name="METHOD", value="PUBLISH"))
        c.extra.append(ContentLine(name="PRODID", value="-//CVFlow-FINAL//VN"))

        e = Event()
        e.uid = f"cvflow-{interview.id}@cvflow.vn"
        e.name = f"PV: {interview.application.job.title}"

        utc_start = interview.start_time - timedelta(hours=7)
        utc_end = interview.end_time - timedelta(hours=7)

        e.begin = utc_start
        e.end = utc_end

        loc = interview.location or "Online"
        if interview.meeting_link:
            loc += f" - Link: {interview.meeting_link}"
        e.location = loc

        e.description = f"Ứng viên {interview.application.candidate.full_name}\nLink: {interview.meeting_link or 'N/A'}"

        c.events.add(e)

        import time

        filename = f"invite_{interview.id}_{int(time.time())}.ics"
        save_path = os.path.join(current_app.root_path, "static", "invites", filename)

        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "w", encoding="utf-8", newline="") as f:
            f.writelines(c.serialize_iter())

        return filename
