from flask import Blueprint

hr_bp = Blueprint("hr", __name__, template_folder="../../templates/hr")

from . import routes
