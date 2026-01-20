from flask import Flask
from config import config
from app.extensions import db, migrate, login_manager, bcrypt, csrf, mail


def create_app(config_name="default"):
    """
    Application Factory: Nơi khởi tạo Flask App.
    """
    app = Flask(__name__)

    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    from app.modules.public import public_bp
    from app.modules.auth import auth_bp
    from app.modules.hr import hr_bp
    from app.modules.candidate import candidate_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(hr_bp, url_prefix="/hr")
    app.register_blueprint(candidate_bp, url_prefix="/candidate")

    with app.app_context():
        from app import models

    return app
