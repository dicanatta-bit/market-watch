"""Market Watch v2 — Database seeding (tables + superadmin)"""
import sys
from config import Config
from app import create_app
from models import db, User
from auth import hash_password


def seed():
    app = create_app(Config)
    with app.app_context():
        print("Creating tables...")
        db.create_all()
        print("✓ All tables created.")

        # Superadmin account
        existing = User.query.filter_by(username=app.config["SUPERADMIN_USERNAME"]).first()
        if existing:
            print(f"✓ Superadmin already exists: {existing.username}")
        else:
            sa = User(
                username=app.config["SUPERADMIN_USERNAME"],
                password_hash=hash_password(app.config["SUPERADMIN_PASSWORD"]),
                role="superadmin",
                nama="Superadmin AJN",
                is_active=True,
                force_pw_change=False,
            )
            db.session.add(sa)
            db.session.commit()
            print(f"✓ Superadmin created: {sa.username}")
            print(f"  Password: {app.config['SUPERADMIN_PASSWORD']}")
            print(f"  ⚠️  Change this in production!")


if __name__ == "__main__":
    seed()
    print("\nDone.")
