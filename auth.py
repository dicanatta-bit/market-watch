"""Market Watch v2 — Authentication (Flask-Login + bcrypt + RBAC)"""
import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
from models import db, User

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Silakan login terlebih dahulu."

auth_bp = Blueprint("auth", __name__, url_prefix="")


def init_auth(app):
    login_manager.init_app(app)
    app.register_blueprint(auth_bp)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(password, password_hash):
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def superadmin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != "superadmin":
            flash("Akses terbatas. Hanya superadmin.", "danger")
            return redirect(url_for("location.dashboard"))
        return f(*args, **kwargs)
    return decorated


def location_admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != "admin_lokasi" and current_user.role != "superadmin":
            flash("Akses terbatas.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


# ── Routes ─────────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("superadmin.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user = User.query.filter_by(username=username, is_active=True).first()

        if user and check_password(password, user.password_hash):
            login_user(user)
            user.last_login = db.func.now()
            db.session.commit()

            if user.force_pw_change:
                flash("Ganti password default Anda.", "warning")
                return redirect(url_for("auth.change_password"))

            if user.role == "superadmin":
                return redirect(url_for("superadmin.dashboard"))
            else:
                return redirect(url_for("location.dashboard", id_lokasi=user.id_lokasi))
        else:
            flash("Username atau password salah.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Berhasil logout.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old = request.form.get("old_password", "").strip()
        new = request.form.get("new_password", "").strip()
        confirm = request.form.get("confirm_password", "").strip()

        if not check_password(old, current_user.password_hash):
            flash("Password lama salah.", "danger")
        elif new != confirm:
            flash("Password baru tidak cocok.", "danger")
        elif len(new) < 6:
            flash("Password minimal 6 karakter.", "danger")
        else:
            current_user.password_hash = hash_password(new)
            current_user.force_pw_change = False
            db.session.commit()
            flash("Password berhasil diubah.", "success")
            return redirect(url_for("location.dashboard"))

    return render_template("change_password.html")
