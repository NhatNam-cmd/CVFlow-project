from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class SalaryToolForm(FlaskForm):
    gross_salary = IntegerField(
        "Thu nhập tháng (Gross)",
        validators=[
            DataRequired(message="Vui lòng nhập mức lương"),
            NumberRange(min=1000000, message="Lương phải lớn hơn 1 triệu VNĐ"),
        ],
    )

    region = SelectField(
        "Vùng (Lương tối thiểu)",
        choices=[
            ("1", "Vùng I (4.960.000đ)"),
            ("2", "Vùng II (4.410.000đ)"),
            ("3", "Vùng III (3.860.000đ)"),
            ("4", "Vùng IV (3.250.000đ)"),
        ],
        default="1",
    )

    dependents = IntegerField(
        "Số người phụ thuộc",
        default=0,
        validators=[NumberRange(min=0, message="Số người không hợp lệ")],
    )

    insurance_type = SelectField(
        "Đóng bảo hiểm trên",
        choices=[("full", "Lương chính thức"), ("other", "Mức khác...")],
        default="full",
    )

    submit = SubmitField("TÍNH TOÁN NGAY")
