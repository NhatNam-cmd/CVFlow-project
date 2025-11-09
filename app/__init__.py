from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
import os

db = SQLAlchemy()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    from .public import bp as public_bp

    app.register_blueprint(public_bp)

    from .admin import bp as admin_bp

    app.register_blueprint(admin_bp, url_prefix="/admin")

    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        os.makedirs(app.config["UPLOAD_FOLDER"])

    with app.app_context():

        from app import models  # noqa: F401

        db.create_all()

    return app
