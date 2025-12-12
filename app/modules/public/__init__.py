from flask import Blueprint

# Khởi tạo Blueprint 'public'
# template_folder trỏ ngược ra ngoài 2 cấp để đến thư mục templates gốc
public_bp = Blueprint("public", __name__, template_folder="../../templates/public")

from . import routes
