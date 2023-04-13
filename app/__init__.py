"""Application initializer."""
# pylint: disable=import-outside-toplevel, unused-import

from os import environ
import sys

import logging

from werkzeug.utils import import_string

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

from dotenv import load_dotenv

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# read .env file with configurations
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
csrf = CSRFProtect()

app = Flask(__name__, instance_relative_config=True)
csrf.init_app(app)


def app_init():
    """Initialise app."""
    cfg = import_string('configmodule.ProductionConfig')()
    if 'SERVER_CONF' in environ:
        cfg = import_string(environ['SERVER_CONF'])()

    app.config.from_object(cfg)

    # initialise sentry interface
    if app.config['SENTRY_HOOK']:
        sentry_sdk.init(
            dsn=app.config['SENTRY_HOOK'],
            environment=environ['SERVER_CONF'].split('.')[1],
            release=app.config['VERSION'],
            traces_sample_rate=app.config['SENTRY_RATE']
        )

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    level = logging.DEBUG if app.config['DEBUG'] else logging.INFO
    log_file = app.config.get('LOG_PATH') if app.config.get('LOG_PATH') else ''
    log_file += 'flask.log'
    # log into STDOUT stream
    if app.config.get('LOG_PATH') == 'STDOUT':
        logging.basicConfig(stream=sys.stdout,
                            format='%(asctime)s\t%(levelname)s\t%(filename)s\t%(message)s',
                            level=level
                            )
    # log into file
    else:
        logging.basicConfig(filename=log_file,
                            format='%(asctime)s\t%(levelname)s\t%(filename)s\t%(message)s',
                            level=level
                            )

    with app.app_context():
        from . import routes
        from . import auth
        from . import settings
        from . import autohooks
        from . import error_handler
        app.register_blueprint(routes.main_bp)
        app.register_blueprint(auth.auth_bp)
        app.register_blueprint(settings.settings_bp)
        app.register_blueprint(autohooks.auto_bp)

        csrf.exempt(autohooks.auto_bp)

        return app
