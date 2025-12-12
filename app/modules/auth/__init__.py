from flask import Blueprint

# Khởi tạo Blueprint 'auth'
# template_folder giúp Flask biết tìm file HTML cho module này ở đâu
# url_prefix='/auth' nghĩa là các route sẽ bắt đầu bằng /auth (ví dụ /auth/login)
# Tuy nhiên, để URL đẹp (vd: /login thay vì /auth/login), ta có thể không set prefix hoặc set root.
# Ở đây ta không set prefix để giữ URL ngắn gọn như bản demo.

auth_bp = Blueprint("auth", __name__, template_folder="../../templates/auth")

from . import routes
