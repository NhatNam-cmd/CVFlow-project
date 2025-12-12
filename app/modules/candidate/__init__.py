from flask import Blueprint

candidate_bp = Blueprint(
    "candidate", __name__, template_folder="../../templates/candidate"
)

from . import routes
