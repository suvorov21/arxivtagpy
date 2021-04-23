"""Application initialiser."""
# pylint: disable=import-outside-toplevel

from  os import environ

import logging

from werkzeug.utils import import_string

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate

from dotenv import load_dotenv

# read .env file with configurations
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()

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
    mail.init_app(app)
    migrate.init_app(app, db)

    level = logging.DEBUG if app.config['DEBUG'] else logging.INFO
    log_file = app.config.get('LOG_PATH') if app.config.get('LOG_PATH') else ''
    log_file += 'flask.log'
    logging.basicConfig(filename=log_file,
                        format='%(asctime)s\t%(levelname)s\t%(filename)s\t%(message)s',
                        level=level
                        )

    with app.app_context():
        from . import routes
        from . import auth
        from . import settings
        app.register_blueprint(routes.main_bp)
        app.register_blueprint(auth.auth_bp)
        app.register_blueprint(settings.settings_bp)

        if app.config['BUILD_ASSETS']:
            from .assets import compile_assets
            compile_assets(app)

        return app
