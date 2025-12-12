from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models.user import User, Company


# 1. Login
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Mật khẩu", validators=[DataRequired()])
    remember_me = BooleanField("Ghi nhớ đăng nhập")
    submit = SubmitField("Đăng nhập")


# 2. Đăng ký Candidate
class CandidateRegisterForm(FlaskForm):
    full_name = StringField(
        "Họ và tên", validators=[DataRequired(), Length(min=2, max=100)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Mật khẩu", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Nhập lại mật khẩu", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Đăng ký Ứng viên")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("Email này đã được sử dụng.")


# 3. Đăng ký HR
class HRRegisterForm(FlaskForm):
    full_name = StringField("Họ tên người liên hệ", validators=[DataRequired()])
    email = StringField("Email công việc", validators=[DataRequired(), Email()])
    password = PasswordField("Mật khẩu", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Nhập lại mật khẩu", validators=[DataRequired(), EqualTo("password")]
    )

    company_name = StringField("Tên Doanh Nghiệp", validators=[DataRequired()])
    tax_number = StringField(
        "Mã Số Thuế", validators=[DataRequired(), Length(min=10, max=14)]
    )
    company_address = StringField("Địa chỉ trụ sở", validators=[DataRequired()])

    submit = SubmitField("Gửi Hồ Sơ Xét Duyệt")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("Email này đã được sử dụng.")

    # Chặn lỗi sập web do trùng MST
    def validate_tax_number(self, tax_number):
        company = Company.query.filter_by(tax_number=tax_number.data).first()
        if company:
            raise ValidationError("Mã số thuế này đã tồn tại trong hệ thống.")
