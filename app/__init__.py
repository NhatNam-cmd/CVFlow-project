from flask import Flask
from config import config
from app.extensions import db, migrate, login_manager, bcrypt, csrf


def create_app(config_name="default"):
    """
    Application Factory: Nơi khởi tạo Flask App.
    """
    app = Flask(__name__)

    # 1. Nạp cấu hình từ config.py
    app.config.from_object(config[config_name])

    # 2. Khởi tạo các Extensions (đã khai báo ở extensions.py)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    # 3. Đăng ký Blueprints (Modules)
    # Chúng ta sẽ bỏ comment phần này sau khi bạn code xong các file routes.py
    from app.modules.public import public_bp
    from app.modules.auth import auth_bp
    from app.modules.hr import hr_bp
    from app.modules.candidate import candidate_bp

    # from app.modules.admin import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(hr_bp, url_prefix="/hr")
    app.register_blueprint(candidate_bp, url_prefix="/candidate")
    # app.register_blueprint(admin_bp)

    # 4. Import Models để Flask-Migrate nhận diện được
    # Lưu ý: Import bên trong hàm để tránh lỗi vòng lặp (circular import)
    with app.app_context():
        from app import models

    return app
