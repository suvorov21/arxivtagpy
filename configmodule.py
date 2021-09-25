"""Configuration settings."""

from os import environ
from datetime import datetime


class Config:
    """Default config."""
    DEBUG = False
    TESTING = False

    # DB
    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # security
    TOKEN = environ.get('TOKEN')
    SECRET_KEY = b'\xed\xb5S\x8c\xc2\x83\xb5>\xe6\xf82\x9e@\x95\xd0\xcb\xfa\x9c\xf7\xafy\xd7\x8d9'
    if environ.get('SECURE_KEY'):
        SECRET_KEY = environ.get('SECURE_KEY').split(',')[0]
    # keep users logged in
    SESSION_PERMANENT = True

    LOG_PATH = environ.get('LOG_PATH')

    assets = environ.get('BUILD_ASSETS')
    BUILD_ASSETS = True if assets == 'True' else False

    SENTRY_HOOK = environ.get('SENTRY_HOOK')
    VERSION = environ.get('VERSION')

    # email config
    MAIL_SERVER = environ.get('MAIL_SERVER')
    MAIL_PORT = environ.get('MAIL_PORT')
    MAIL_USERNAME = environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = environ.get('MAIL_DEFAULT_SENDER')

    MAIL_USE_SSL = False
    MAIL_USE_TLS = True

    time_str = '6:30'
    if environ.get('UPDATE_TIME'):
        time_str = environ.get('UPDATE_TIME')
    UPDATE_TIME = datetime.strptime(time_str,
                                    '%H:%M'
                                    ).time()


class ProductionConfig(Config):
    """Prod config."""
    PROD = True


class DevelopmentConfig(Config):
    """Dev config."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL_DEBUG')
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True


class TestingConfig(Config):
    """Testing (staging) config."""
    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL_TEST')
    WTF_CSRF_ENABLED = False
    DEBUG = True
    TESTING = True
