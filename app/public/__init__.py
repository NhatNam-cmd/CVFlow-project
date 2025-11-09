from flask import Blueprint

bp = Blueprint("public", __name__, template_folder="../templates/public")


from app.public import routes  # noqa: F401, E402
