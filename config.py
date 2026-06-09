"""Market Watch v2 — Configuration"""
import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "mw-dev-secret-change-in-production")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://mw_app:mw_password_2026@localhost/market_watch?charset=utf8mb4",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 5,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
    }

    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload

    EKNMP_USERNAME = os.environ.get("EKNMP_USERNAME", "agrinas")
    EKNMP_PASSWORD = os.environ.get("EKNMP_PASSWORD", "agrin4s$")

    SUPERADMIN_USERNAME = os.environ.get("SUPERADMIN_USERNAME", "superadmin@ajn.id")
    SUPERADMIN_PASSWORD = os.environ.get("SUPERADMIN_PASSWORD", "admin123")

    OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
