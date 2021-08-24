"""Application initialiser."""
# pylint: disable=import-outside-toplevel

from  os import environ
import sys

import logging

import click

from werkzeug.utils import import_string

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate

from dotenv import load_dotenv

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# read .env file with configurations
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()

app = Flask(__name__, instance_relative_config=True)

@app.cli.command("create-db")
def create_db():
    """CLI for database creation."""
    db.init_app(app)
    db.create_all()
    db.session.commit()

def app_init():
    """Initialise app."""

    if 'SERVER_CONF' in environ:
        cfg = import_string(environ['SERVER_CONF'])()
    else:
        cfg = import_string('configmodule.ProductionConfig')()

    app.config.from_object(cfg)

    # initialise sentry interface
    if app.config['SENTRY_HOOK']:
        sentry_sdk.init(
            dsn=app.config['SENTRY_HOOK'],
            integrations=[FlaskIntegration()],
            environment=environ['SERVER_CONF'].split('.')[1],
            release=app.config['VERSION'],

            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            # We recommend adjusting this value in production.
            traces_sample_rate=1.0
        )

    if app.config.get('SQLALCHEMY_DATABASE_URI') is None:
        logging.error("Database URL is not specified.")
        return

    # fix a syntax for database
    if 'postgres://' in app.config['SQLALCHEMY_DATABASE_URI']:
        app.config['SQLALCHEMY_DATABASE_URI'] = \
        app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://',
                                                      'postgresql://'
                                                      )

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    if "Development" in environ['SERVER_CONF'] or "Production" in environ['SERVER_CONF']:
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
        app.register_blueprint(routes.main_bp)
        app.register_blueprint(auth.auth_bp)
        app.register_blueprint(settings.settings_bp)
        app.register_blueprint(autohooks.auto_bp)

        if app.config['BUILD_ASSETS']:
            from .assets import compile_assets
            compile_assets(app)

        return app
