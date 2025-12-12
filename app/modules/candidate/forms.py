from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, FileField
from wtforms.validators import Length, Optional, Regexp
from flask_wtf.file import FileAllowed, FileRequired


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
    submit = SubmitField("Lưu Thay Đổi")


class CVUploadForm(FlaskForm):
    cv_file = FileField(
        "Chọn CV (PDF/DOCX)",
        validators=[
            FileRequired(message="Vui lòng chọn file."),
            FileAllowed(["pdf", "docx", "doc"], "Chỉ chấp nhận file PDF hoặc Word."),
        ],
    )
    submit = SubmitField("Tải Lên")
