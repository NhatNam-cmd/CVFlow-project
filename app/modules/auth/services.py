from app.extensions import db
from app.models.user import User, Company


class AuthService:

    @staticmethod
    def create_candidate(data):
        user = User(full_name=data["full_name"], email=data["email"], role="CANDIDATE")
        # Gán password riêng để kích hoạt Setter mã hóa
        user.password = data["password"]

        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def create_hr_with_company(hr_data, company_data):
        try:
            # 1. Tạo Company
            company = Company(
                name=company_data["name"],
                tax_number=company_data["tax_number"],
                address=company_data["address"],
                verification_status="PENDING",
            )
            db.session.add(company)
            db.session.flush()  # Lấy ID

            # 2. Tạo User HR
            user = User(
                email=hr_data["email"],
                full_name=hr_data["full_name"],
                role="HR",
                company_id=company.id,
            )
            user.password = hr_data["password"]  # Gán password riêng

            db.session.add(user)
            db.session.commit()
            return user

        except Exception as e:
            db.session.rollback()
            raise e
