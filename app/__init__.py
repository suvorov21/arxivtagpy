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

    if 'SERVER_CONF' in environ:
        cfg = import_string(environ['SERVER_CONF'])()
    else:
        cfg = import_string('configmodule.ProductionConfig')()

    app.config.from_object(cfg)

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from . import routes
        app.register_blueprint(routes.main_bp)

        if app.config['DEBUG']:
            from .assets import compile_assets
            compile_assets(app)

        db.create_all()

        return app
