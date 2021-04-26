"""Test fixtures go there."""
# pylint: disable=redefined-outer-name

import multiprocessing
from datetime import datetime

from werkzeug.utils import import_string
from werkzeug.security import generate_password_hash

from flask import url_for
import pytest

from app import app_init, db
from app.model import User, Tag

EMAIL = 'tester@gmail.com'
PASS = 'tester' # nosec

TMP_EMAIL = 'tmp_tester@gmail.com'

def make_user(email):
    """Make a default user."""
    user1 = User(email=email,
                 pasw=generate_password_hash(PASS),
                 created=datetime.now(),
                 login=datetime.now(),
                 arxiv_cat=['hep-ex'],
                 pref='{"tex": "True"}'
                 )
    tag = Tag(name='test',
              rule='ti{math}|abs{physics}&au{John}',
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
    """Initialize app + user recrod in db."""
    multiprocessing.set_start_method("fork")
    app = app_init()
    cfg = import_string('configmodule.TestingConfig')
    app.config.from_object(cfg)
    with app.app_context():
        db.create_all()
        user = make_user(EMAIL)
        db.session.add(user)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def login(client):
    """Login user to access the personal data."""
    client.post(url_for('auth_bp.login'),
                data={'i_login': EMAIL,
                      'i_pass': PASS
                      },
                follow_redirects=True
                )
    yield client
    client.get('/logout',
               follow_redirects=True
               )

@pytest.fixture(scope='function')
def tmp_user(client):
    """Fixture for tmp user that could be changed/deleted."""
    user = make_user(TMP_EMAIL)
    db.session.add(user)
    db.session.commit()
    client.post(url_for('auth_bp.login'),
                data={'i_login': TMP_EMAIL,
                      'i_pass': PASS
                      },
                follow_redirects=True
                )
    yield client
    User.query.filter_by(email=TMP_EMAIL).delete()
    db.session.commit()