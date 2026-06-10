"""Seed — create tables + superadmin"""
import sys; sys.path.insert(0, ".")
from app.main import init_db
from app.database import SessionLocal
from app.models import User
from app.auth import hash_password
from app.config import SUPERADMIN_USERNAME, SUPERADMIN_PASSWORD

init_db()
db = SessionLocal()
try:
    existing = db.query(User).filter_by(username=SUPERADMIN_USERNAME).first()
    if not existing:
        db.add(User(username=SUPERADMIN_USERNAME, password_hash=hash_password(SUPERADMIN_PASSWORD),
                     role="superadmin", nama="Superadmin AJN", is_active=True, force_pw_change=False))
        db.commit()
        print(f"✓ Superadmin: {SUPERADMIN_USERNAME}")
    else:
        print(f"✓ Superadmin exists")
finally:
    db.close()
