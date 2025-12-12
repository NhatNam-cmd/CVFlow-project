from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect

# Khởi tạo các Extension (chưa gắn vào App)
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
csrf = CSRFProtect()
login_manager = LoginManager()

# Cấu hình cho Login Manager
login_manager.login_view = "auth.login"  # Nếu chưa đăng nhập thì đá về trang này
login_manager.login_message = "Vui lòng đăng nhập để truy cập trang này."
login_manager.login_message_category = "warning"


# Hàm này sẽ được gọi ở models/user.py để load user từ DB
@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User

    return User.query.get(int(user_id))
