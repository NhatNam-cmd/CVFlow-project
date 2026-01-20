from app.models.scheduler import Interview, Availability
from app.models.application import Application
from app.models.user import User
from datetime import datetime, timedelta, time


class SchedulerEngine:
    @staticmethod
    def check_conflict(
        recruiter_id,
        candidate_id,
        start_time,
        duration_minutes,
        exclude_interview_id=None,
    ):
        """
        Thêm tham số exclude_interview_id để bỏ qua chính cuộc họp đang sửa
        """
        end_time = start_time + timedelta(minutes=duration_minutes)

        query_hr = Interview.query.filter(
            Interview.recruiter_id == recruiter_id,
            Interview.status != "CANCELLED",
            Interview.start_time < end_time,
            Interview.end_time > start_time,
        )

        if exclude_interview_id:
            query_hr = query_hr.filter(Interview.id != exclude_interview_id)

        hr_conflict = query_hr.first()

        if hr_conflict:
            return (
                True,
                f"HR đang bận: {hr_conflict.application.candidate.full_name} "
                f"({hr_conflict.start_time.strftime('%H:%M')})",
            )

        query_cand = Interview.query.join(Application).filter(
            Application.user_id == candidate_id,
            Interview.status != "CANCELLED",
            Interview.start_time < end_time,
            Interview.end_time > start_time,
        )

        if exclude_interview_id:
            query_cand = query_cand.filter(Interview.id != exclude_interview_id)

        candidate_conflict = query_cand.first()

        if candidate_conflict:
            return (
                True,
                f"Ứng viên bận lịch khác ({candidate_conflict.start_time.strftime('%H:%M')})",
            )

        return False, None

    @staticmethod
    def is_within_working_hours(candidate_id, start_time, duration_minutes):
        """
        (Nâng cao) Kiểm tra xem giờ hẹn có nằm trong khung giờ rảnh candidate cài đặt không.
        Lưu ý: Đây chỉ là cảnh báo (Soft check), HR vẫn có thể book đè nếu cần gấp.
        """
        candidate = User.query.get(candidate_id)
        if not candidate or not candidate.available_days:
            return True  # Nếu không cài đặt gì thì coi như rảnh

        day_map = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
        current_day_str = day_map[start_time.weekday()]

        if current_day_str not in candidate.available_days:
            pass

        return True

    @staticmethod
    def get_suggested_slots(
        recruiter_id, candidate_id, duration_minutes=60, days_ahead=7
    ):
        suggestions = []
        today = datetime.now().date()

        hr_map = SchedulerEngine._get_user_availability_map(recruiter_id)
        cand_map = SchedulerEngine._get_user_availability_map(candidate_id)

        print(f"🗓 [DEBUG] HR Map: {hr_map.keys()}")
        print(f"🗓 [DEBUG] Cand Map: {cand_map.keys()}")
        if not hr_map:
            return {"error": "HR_NO_SETTINGS"}  # HR chưa cài lịch
        if not cand_map:
            return {"error": "CANDIDATE_NO_SETTINGS"}

        for i in range(1, days_ahead + 1):
            current_date = today + timedelta(days=i)
            weekday = current_date.weekday()  # Python trả về: 0=Mon, 6=Sun

            hr_slot = hr_map.get(weekday)
            cand_slot = cand_map.get(weekday)

            if not hr_slot or not cand_slot:
                continue

            start_max = max(hr_slot["start"], cand_slot["start"])
            end_min = min(hr_slot["end"], cand_slot["end"])

            if start_max >= end_min:
                continue

            current_dt = datetime.combine(current_date, start_max)
            end_dt = datetime.combine(current_date, end_min)

            while current_dt + timedelta(minutes=duration_minutes) <= end_dt:
                is_busy, _ = SchedulerEngine.check_conflict(
                    recruiter_id, candidate_id, current_dt, duration_minutes
                )
                if not is_busy:
                    suggestions.append(
                        {
                            "date": current_date.strftime("%d/%m/%Y"),
                            "weekday": current_date.strftime("%A"),
                            "start": current_dt.strftime("%H:%M"),
                            "end": (
                                current_dt + timedelta(minutes=duration_minutes)
                            ).strftime("%H:%M"),
                            "value": current_dt.strftime("%Y-%m-%dT%H:%M"),
                        }
                    )
                    if len(suggestions) >= 5:
                        return suggestions
                current_dt += timedelta(minutes=30)

        return suggestions

    @staticmethod
    def _get_user_availability_map(user_id):
        """
        Lấy lịch rảnh và chuẩn hóa về: 0=Mon ... 6=Sun
        """
        avail_list = Availability.query.filter_by(user_id=user_id).all()
        if avail_list:
            return {
                a.day_of_week: {"start": a.start_time, "end": a.end_time}
                for a in avail_list
            }

        user = User.query.get(user_id)
        if user and user.available_days:
            day_str_map = {
                "Mon": 0,
                "Tue": 1,
                "Wed": 2,
                "Thu": 3,
                "Fri": 4,
                "Sat": 5,
                "Sun": 6,
            }
            result_map = {}
            u_start = user.start_time or time(8, 0)
            u_end = user.end_time or time(17, 0)

            for day_code in user.available_days.split(","):
                day_code = day_code.strip()
                if day_code in day_str_map:
                    result_map[day_str_map[day_code]] = {"start": u_start, "end": u_end}
            return result_map

        return {}

    @staticmethod
    def _build_availability_map(avail_list):
        """Helper: Chuyển List DB thành Dictionary cho dễ tra cứu"""
        if not avail_list:
            return {}
        return {
            a.day_of_week: {"start": a.start_time, "end": a.end_time}
            for a in avail_list
        }
