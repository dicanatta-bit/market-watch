"""Market Watch v2 — Flask Application Factory"""
import os
from flask import Flask
from config import Config
from models import db
from auth import init_auth


def create_app(config_class=None):
    app = Flask(__name__)

    if config_class is None:
        config_class = Config
    app.config.from_object(config_class)

    db.init_app(app)
    init_auth(app)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["OUTPUT_DIR"], exist_ok=True)

    # Register blueprints
    from blueprints.superadmin import superadmin_bp
    from blueprints.location import location_bp
    from blueprints.api import api_bp
    from blueprints.export import export_bp

    app.register_blueprint(superadmin_bp)
    app.register_blueprint(location_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(export_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
