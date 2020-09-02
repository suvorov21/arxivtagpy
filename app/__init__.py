from  os import environ

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from werkzeug.utils import import_string

db = SQLAlchemy()
login_manager = LoginManager()

def app_init():
    """Initialise app."""
    app = Flask(__name__, instance_relative_config=True)

    if 'SERVER_CONF' not in environ or \
        'DATABASE_URL' not in environ:
        print("App configuration error!")
        return None

    cfg = import_string(environ['SERVER_CONF'])()
    app.config.from_object(cfg)

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from . import routes
        app.register_blueprint(routes.main_bp)

        from .assets import compile_assets
        compile_assets(app)

        db.create_all()

        return app
