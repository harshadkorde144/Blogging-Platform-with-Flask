import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

try:  # load variables from a local .env file if python-dotenv is installed
    from dotenv import load_dotenv
    load_dotenv(os.path.join(basedir, ".env"))
except ImportError:
    pass

_secure = os.environ.get("COOKIE_SECURE", "false").lower() == "true"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(basedir, "app.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    POSTS_PER_PAGE = 6
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # reject request bodies > 1 MB
    # Session / cookie security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _secure
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = _secure


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret"
    POSTS_PER_PAGE = 5
