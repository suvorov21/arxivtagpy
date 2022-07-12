"""Test fixtures go there."""
# pylint: disable=redefined-outer-name

import multiprocessing
from datetime import datetime, timedelta
import logging
import requests

from werkzeug.utils import import_string
from werkzeug.security import generate_password_hash

from flask import url_for
import pytest

from app import app_init, db, mail
from app.interfaces.model import User, Tag

EMAIL = 'arxiv_tester@mailinator.com'
PASS = 'tester'  # nosec

TMP_EMAIL = 'arxiv_tester2@mailinator.com'
TMP_PASS = 'tester' #nosec

DEFAULT_LIST = 'Favourite'


def make_user(email):
    """Make a default user."""
    user1 = User(email=email,
                 pasw=generate_password_hash(PASS),
                 created=datetime.now(),
                 login=datetime.now(),
                 last_paper=datetime.now() - timedelta(days=4),
                 arxiv_cat=['hep-ex'],
                 pref='{"tex": "True"}',
                 recent_visit=0,
                 verified_email=False
                 )
    tag = Tag(name='test',
              rule='ti{math}|abs{physics&math}&au{!John}',
              color='#ff0000',
              order=0,
              public=True,
              email=True,
              bookmark=True
              )
    user1.tags.append(tag)
    return user1


@pytest.fixture(scope='session', autouse=True)
def app():
    """Initialize app + user record in db."""
    multiprocessing.set_start_method("fork")
    app = app_init()
    cfg = import_string('configmodule.TestingConfig')
    app.config.from_object(cfg)
    logging.level = logging.DEBUG
    with app.app_context():
        mail.init_app(app)
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def user(client):
    """Registered user ficture."""
    client.post(url_for('auth_bp.new_user'),
                data={'email': EMAIL,
                      'pasw': PASS,
                      'pasw2': PASS
                      },
                )
    yield User.query.filter_by(email=EMAIL).first()
    User.query.filter_by(email=EMAIL).delete()
    db.session.commit()


@pytest.fixture(scope='function')
def login(client, user):
    """Login user to access the personal data."""
    client.post(url_for('auth_bp.login'),
                data={'i_login': user.email,
                      'i_pass': PASS
                      },
                )
    yield client
    client.get('/logout')


@pytest.fixture(scope='function')
def tmp_user(client):
    """Fixture for tmp user that could be changed/deleted."""
    client.post(url_for('auth_bp.new_user'),
                data={'email': TMP_EMAIL,
                      'pasw': PASS,
                      'pasw2': PASS
                      },
                )
    yield User.query.filter_by(email=TMP_EMAIL).first()
    User.query.filter_by(email=TMP_EMAIL).delete()
    db.session.commit()


@pytest.fixture(scope='function')
def tmp_login(client, tmp_user):
    """Login user to access the personal data."""
    client.post(url_for('auth_bp.login'),
                data={'i_login': tmp_user.email,
                      'i_pass': PASS
                      },
                )
    yield client
    client.get('/logout')


@pytest.fixture(scope='module')
def papers(app):
    """Papers downloader."""
    with app.app_context(), app.test_request_context():
        requests.post(url_for('auto_bp.load_papers', # nosec
                              token='test_token',  # nosec
                              n_papers=500,
                              set='physics:hep-ex',
                              _external=True
                              )
                      )
