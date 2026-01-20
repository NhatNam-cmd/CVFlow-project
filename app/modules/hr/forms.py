from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, URL
from wtforms.validators import NumberRange


class CompanyProfileForm(FlaskForm):
    name = StringField("Tên hiển thị công ty", validators=[DataRequired()])
    industry = SelectField(
        "Lĩnh vực (Industry)",
        choices=[
            ("Outsourcing", "IT Outsourcing"),
            ("Product", "IT Product (SaaS)"),
            ("Fintech", "Fintech / Banking"),
            ("E-commerce", "E-commerce"),
            ("Telco", "Telecommunication"),
        ],
    )
    website = StringField("Website", validators=[Optional(), URL()])
    address = StringField("Địa chỉ trụ sở")
    description = TextAreaField("Giới thiệu công ty")
    submit = SubmitField("Lưu Thay Đổi")


class JobPostForm(FlaskForm):
    title = StringField(
        "Chức danh (Job Title)", validators=[DataRequired(), Length(max=200)]
    )
    min_years_experience = IntegerField(
        "Kinh nghiệm (Năm)",
        validators=[NumberRange(min=0, message="Phải là số dương")],
        default=0,
    )
    level = SelectField(
        "Cấp bậc",
        choices=[
            ("Fresher", "Fresher"),
            ("Junior", "Junior"),
            ("Senior", "Senior"),
            ("Lead", "Lead/Manager"),
        ],
    )
    location = SelectField(
        "Địa điểm",
        choices=[
            ("Hà Nội", "Hà Nội"),
            ("Hồ Chí Minh", "Hồ Chí Minh"),
            ("Đà Nẵng", "Đà Nẵng"),
            ("Remote", "Remote"),
        ],
    )
    test_question = StringField("Câu hỏi trắc nghiệm (Tùy chọn)")
    option1 = StringField("Đáp án A")
    option2 = StringField("Đáp án B")
    option3 = StringField("Đáp án C")
    option4 = StringField("Đáp án D")
    correct_answer = SelectField(
        "Đáp án đúng", choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")]
    )

    salary_min = IntegerField("Lương từ (VNĐ)", validators=[Optional()])
    salary_max = IntegerField("Đến (VNĐ)", validators=[Optional()])

    description = TextAreaField("Mô tả công việc", validators=[DataRequired()])
    requirements = TextAreaField("Yêu cầu ứng viên", validators=[DataRequired()])
    benefits = TextAreaField("Quyền lợi")

    skills_required = StringField(
        "Kỹ năng bắt buộc (cách nhau bằng dấu phẩy)", validators=[DataRequired()]
    )

    submit = SubmitField("Đăng Tin Ngay")
