from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import (
    StringField,
    TextAreaField,
    SubmitField,
    FileField,
    TimeField,
    SelectMultipleField,
    widgets,
)
from wtforms.validators import Length, Optional, Regexp


class MultiCheckboxField(SelectMultipleField):
    """
    Field tùy chỉnh để hiển thị SelectMultipleField dưới dạng danh sách các checkbox
    thay vì list box mặc định của HTML.
    """

    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class CandidateProfileForm(FlaskForm):
    phone = StringField(
        "Số điện thoại",
        validators=[
            Optional(),
            Length(min=9, max=15, message="Số điện thoại không hợp lệ."),
            Regexp(r"^[0-9+]+$", message="Số điện thoại chỉ được chứa số."),
        ],
    )

    bio = TextAreaField(
        "Giới thiệu bản thân",
        validators=[
            Optional(),
            Length(max=500, message="Bio không được quá 500 ký tự."),
        ],
    )

    available_days = MultiCheckboxField(
        "Ngày rảnh trong tuần",
        choices=[
            ("Mon", "Thứ 2"),
            ("Tue", "Thứ 3"),
            ("Wed", "Thứ 4"),
            ("Thu", "Thứ 5"),
            ("Fri", "Thứ 6"),
            ("Sat", "Thứ 7"),
            ("Sun", "Chủ Nhật"),
        ],
        validators=[Optional()],
    )

    start_time = TimeField(
        "Từ giờ",
        validators=[Optional()],
        format="%H:%M",  # Định dạng giờ phút (VD: 09:30)
    )

    end_time = TimeField("Đến giờ", validators=[Optional()], format="%H:%M")

    submit = SubmitField("Lưu Hồ Sơ")


class CVUploadForm(FlaskForm):
    cv_file = FileField(
        "Chọn CV (PDF/DOCX)",
        validators=[
            FileRequired(message="Vui lòng chọn file."),
            FileAllowed(["pdf", "docx", "doc"], "Chỉ chấp nhận file PDF hoặc Word."),
        ],
    )
    submit = SubmitField("Tải Lên")
