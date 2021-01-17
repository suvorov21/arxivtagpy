from os import environ

class Config(object):
    """
    Default config.
    """
    DEBUG = False
    TESTING = False

    # DB
    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # security
    def_key = b'\xed\xb5S\x8c\xc2\x83\xb5>\xe6\xf82\x9e@\x95\xd0\xcb\xfa\x9c\xf7\xafy\xd7\x8d9'
    SECRET_KEY = environ.get('SECRET_KEY') if environ.get('SECRET_KEY') else def_key
    SESSION_PERMANENT = True

    # email config


class ProductionConfig(Config):
    """
    Prod config.
    """
    pass

class DevelopmentConfig(Config):
    """
    Dev config.
    """
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True

class TestingConfig(Config):
    """
    Testing (staging) config.
    """
    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL_TEST')
    TESTING = True
