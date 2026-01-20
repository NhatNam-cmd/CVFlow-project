from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, NumberRange


class SalaryToolForm(FlaskForm):
    gross_salary = IntegerField(
        "Thu nhập", validators=[DataRequired(), NumberRange(min=0)]
    )

    dependents = IntegerField(
        "Người phụ thuộc", default=0, validators=[NumberRange(min=0)]
    )

    region = SelectField(
        "Vùng",
        choices=[
            ("1", "Vùng I"),
            ("2", "Vùng II"),
            ("3", "Vùng III"),
            ("4", "Vùng IV"),
        ],
        default="1",
    )

    calc_mode = HiddenField("Mode", default="GROSS_TO_NET")

    submit = SubmitField("Tính toán")
