import os

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager

from models import User, db
from routes.auth import auth_bp
from routes.books import books_bp
from flask_wtf import CSRFProtect
csrf_token = CSRFProtect()

load_dotenv()

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)

    if test_config is None:
        app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
    else:
        app.config.update(test_config)

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    csrf_token = CSRFProtect(app)

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(books_bp)
    app.register_blueprint(auth_bp)

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
