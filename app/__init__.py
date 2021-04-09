from  os import environ

import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
# from flask_mail import Mail
from flask_migrate import Migrate

from werkzeug.utils import import_string

from dotenv import load_dotenv

# read .env file with configurations
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
# mail = Mail()
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
    # mail.init_app(app)
    migrate.init_app(app, db)

    level = logging.DEBUG if app.config['DEBUG'] else logging.INFO
    logging.basicConfig(filename='flask.log',
                        format='%(asctime)s\t%(levelname)s\t%(filename)s\t%(message)s',
                        level=level
                        )

    with app.app_context():
        from . import routes
        from . import auth
        app.register_blueprint(routes.main_bp)
        app.register_blueprint(auth.auth_bp)

        if app.config['DEBUG']:
            from .assets import compile_assets
            compile_assets(app)

        return app
