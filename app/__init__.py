import logging

from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError

from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"
login_manager.session_protection = "strong"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.testing:
        logging.basicConfig(level=logging.INFO,
                            format="%(asctime)s %(levelname)s %(name)s: %(message)s")
        if app.config["SECRET_KEY"] == "dev-secret-change-me":
            app.logger.warning("Using the default SECRET_KEY - set SECRET_KEY in production!")

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app import models  # noqa: F401  (needed so migrations see the models)
    from app.auth import bp as auth_bp
    from app.cli import register_cli
    from app.main import bp as main_bp
    from app.utils import register_filters

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp)
    register_filters(app)
    register_cli(app)

    def error_page(code, message):
        return render_template("error.html", code=code, message=message), code

    @app.errorhandler(403)
    def forbidden(e):
        return error_page(403, "You are not allowed to do that.")

    @app.errorhandler(404)
    def not_found(e):
        return error_page(404, "The page you are looking for does not exist.")

    @app.errorhandler(413)
    def too_large(e):
        return error_page(413, "The submitted content is too large.")

    @app.errorhandler(CSRFError)
    def csrf_error(e):
        return error_page(400, "Your session expired. Please go back, refresh the page and try again.")

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return error_page(500, "Something went wrong on our side. Please try again.")

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return resp

    return app
