from flask import Flask
from config import config
from app.extensions import db, migrate, login_manager, bcrypt, csrf


def create_app(config_name="default"):
    """
    Application Factory: Nơi khởi tạo Flask App theo chuẩn Enterprise.
    """
    app = Flask(__name__)

    # 1. Nạp cấu hình từ file config.py
    app.config.from_object(config[config_name])

    # 2. Khởi tạo các Extensions (Database, Login, Security...)
    # Đây là lúc 'db' được gắn linh hồn vào xác (bind with app)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    # 3. Đăng ký Blueprints (Modules)
    # Tạm thời comment lại để tránh lỗi import khi các module còn trống
    # Chúng ta sẽ mở lại từng cái một khi code đến phần đó.

    from app.modules.auth import auth_bp

    app.register_blueprint(auth_bp)

    from app.modules.public import public_bp

    app.register_blueprint(public_bp)

    from app.modules.hr import hr_bp

    app.register_blueprint(hr_bp)

    from app.modules.candidate import candidate_bp

    app.register_blueprint(candidate_bp)

    # from app.modules.admin import admin_bp
    # app.register_blueprint(admin_bp, url_prefix='/admin')

    # 4. Nạp Models
    # Bước này cực quan trọng để Flask-Migrate nhìn thấy các bảng database
    with app.app_context():
        # Import package 'models' sẽ chạy file app/models/__init__.py
        from app import models

    return app
