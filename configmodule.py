"""Configuration settings."""

from os import environ

class Config():
    """Default config."""
    DEBUG = False
    TESTING = False

    # DB
    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # security
    TOKEN = environ.get('TOKEN')
    def_key = b'\xed\xb5S\x8c\xc2\x83\xb5>\xe6\xf82\x9e@\x95\xd0\xcb\xfa\x9c\xf7\xafy\xd7\x8d9'
    SECRET_KEY = environ.get('SECRET_KEY') if environ.get('SECRET_KEY') else def_key
    # keep users logged in
    SESSION_PERMANENT = True

    # email config
    MAIL_SERVER = environ.get('MAIL_SERVER')
    MAIL_PORT = environ.get('MAIL_PORT')
    MAIL_USE_SSL = environ.get('MAIL_USE_SSL')
    MAIL_USERNAME = environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = environ.get('MAIL_DEFAULT_SENDER')

class ProductionConfig(Config):
    """Prod config."""
    pass

class DevelopmentConfig(Config):
    """Dev config."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL_DEBUG')
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True

class TestingConfig(Config):
    """Testing (staging) config."""
    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL_TEST')
    TESTING = True
