from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app.extensions import db
from app.modules.auth import auth_bp
from app.models.user import User, Company
from app.modules.auth.forms import LoginForm, HRRegisterForm, CandidateRegisterForm
from app.modules.auth.services import AuthService


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.role == "HR":
            return redirect(url_for("hr.dashboard"))
        return redirect(url_for("public.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            if user.role == "HR":
                company = db.session.get(Company, user.company_id)
                if company.verification_status == "PENDING":
                    return render_template("auth/pending_approval.html", user=user)
                elif company.verification_status == "REJECTED":
                    flash("Tài khoản bị từ chối.", "danger")
                    return render_template("auth/login.html", form=form)

            login_user(user, remember=form.remember_me.data)

            next_page = request.args.get("next")
            if not next_page or not next_page.startswith("/"):
                if user.role == "HR":
                    return redirect(url_for("hr.dashboard"))
                return redirect(url_for("public.index"))
            return redirect(next_page)

        else:
            flash("Sai email hoặc mật khẩu.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/register/candidate", methods=["GET", "POST"])
def register_candidate():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = CandidateRegisterForm()
    if form.validate_on_submit():
        try:
            AuthService.create_candidate(
                {
                    "full_name": form.full_name.data,
                    "email": form.email.data,
                    "password": form.password.data,
                }
            )
            flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            flash(f"Lỗi hệ thống: {str(e)}", "danger")

    return render_template("auth/register_candidate.html", form=form)


@auth_bp.route("/register/hr", methods=["GET", "POST"])
def register_hr():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = HRRegisterForm()
    if form.validate_on_submit():
        try:
            hr_data = {
                "email": form.email.data,
                "full_name": form.full_name.data,
                "password": form.password.data,
            }
            company_data = {
                "name": form.company_name.data,
                "tax_number": form.tax_number.data,
                "address": form.company_address.data,
            }

            user = AuthService.create_hr_with_company(hr_data, company_data)
            return render_template("auth/register_success.html", email=user.email)

        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi hệ thống: {str(e)}", "danger")

    return render_template("auth/register_hr.html", form=form)


@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("Đã đăng xuất.", "info")
    return redirect(url_for("public.index"))
