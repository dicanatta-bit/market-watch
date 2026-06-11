"""Market Watch v3 — FastAPI + MySQL backend"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://market_watch:Jaladri%2126@localhost/db_market_watch?charset=utf8mb4",
)

SECRET_KEY = os.environ.get("SECRET_KEY", "mw-v3-dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

EKNMP_USERNAME = os.environ.get("EKNMP_USERNAME", "agrinas")
EKNMP_PASSWORD = os.environ.get("EKNMP_PASSWORD", "agrin4s$")

SUPERADMIN_USERNAME = os.environ.get("SUPERADMIN_USERNAME", "superadmin@ajn.id")
SUPERADMIN_PASSWORD = os.environ.get("SUPERADMIN_PASSWORD", "admin123")

UPLOAD_DIR = os.path.join(PROJECT_ROOT, "uploads")
DEFAULT_PASSWORD_PATTERN = "knmp_{id_lokasi}2026"
