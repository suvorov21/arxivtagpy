import os
# import tempfile
import pytest

from werkzeug.utils import import_string
from werkzeug.security import generate_password_hash

from app import app_init, db
from app.model import User

@pytest.fixture
def test_client():
    app = app_init()
    cfg = import_string('configmodule.TestingConfig')
    app.config.from_object(cfg)
    with app.app_context():
        db.create_all()
        user1 = User(email='tester@gmail.com',
                 pasw=generate_password_hash('tester'),
                 arxiv_cat=['hep-ex'],
                 tags='[{"name": "test", "rule":"ti{test}", "color":"#ff0000"}]',
                 pref='{"tex":"True", "easy_and":"True"}'
                 )
        db.session.add(user1)
        db.session.commit()
        testing_client = app.test_client()
        yield testing_client
        db.session.remove()
        db.drop_all()

def test_general(test_client):
    response = test_client.get('/')
    assert response.status_code == 200

def test_log(test_client):
    response = test_client.post('/login',
                                data={'i_login': 'tester@gmail.com', 'i_pass':'tester'},
                                follow_redirects=True
                                )
    assert response.status_code == 200

def test_data(test_client):
    response = test_client.post('/login',
                                data={'i_login': 'tester@gmail.com', 'i_pass':'tester'},
                                follow_redirects=True
                                )
    response = test_client.get('/data?date=today')
    assert response.status_code == 200
