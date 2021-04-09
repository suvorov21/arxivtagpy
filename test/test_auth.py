import os
import pytest

from werkzeug.utils import import_string
from werkzeug.security import generate_password_hash

from flask import session

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
                 pref='{"tex": "True"}'
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

def test_logout(test_client):
    response = test_client.post('/login',
                                data={'i_login': 'tester@gmail.com', 'i_pass':'tester'},
                                follow_redirects=True
                                )

    response = test_client.get('/logout',
                               follow_redirects=True)
    assert response.status_code == 200

def test_newAcc(test_client):
    response = test_client.post('/new_user',
                                data={'email': 'tester2@gmail.com',
                                      'pasw': 'tester2',
                                      'pasw2': 'tester2'
                                      },
                                      follow_redirects=True
                                      )
    assert response.status_code == 200
    assert 'ERROR' not in response.get_data(as_text=True)
    assert 'Welcome' in response.get_data(as_text=True)

def test_delAcc(test_client):
    response = test_client.post('/delAcc',
                                follow_redirects=True
                                )
    assert response.status_code == 200

def test_change_pass(test_client):
    response = test_client.post('/login',
                                data={'i_login': 'tester@gmail.com', 'i_pass':'tester'},
                                follow_redirects=True
                                )

    response = test_client.post('/change_pasw',
                                data={'oldPass': 'tester',
                                      'newPass1': 'tester_new',
                                      'newPass2': 'tester_new'
                                      },
                                follow_redirects=True
                                )
    assert response.status_code == 200
    assert 'ERROR' not in response.get_data(as_text=True)
    assert 'successfully' in response.get_data(as_text=True)

def test_unauthorised_request(test_client):
    response = test_client.post('/change_pasw',
                                data={'oldPass': 'tester',
                                      'newPass1': 'tester_new',
                                      'newPass2': 'tester_new'
                                      },
                                follow_redirects=True
                                )
    assert response.status_code == 200
    assert 'ERROR' in response.get_data(as_text=True)

def test_change_wrong_pass(test_client):
    response = test_client.post('/login',
                                data={'i_login': 'tester@gmail.com', 'i_pass':'tester'},
                                follow_redirects=True
                                )

    response = test_client.post('/change_pasw',
                                data={'oldPass': 'tester_wrong',
                                      'newPass1': 'tester_new',
                                      'newPass2': 'tester_new'
                                      },
                                follow_redirects=True
                                )
    assert response.status_code == 200
    assert 'ERROR! Wrong' in response.get_data(as_text=True)

    response = test_client.post('/change_pasw',
                                data={'oldPass': 'tester',
                                      'newPass1': 'tester_new',
                                      'newPass2': 'tester_new_other'
                                      },
                                follow_redirects=True
                                )
    assert response.status_code == 200
    assert 'don\'t match!' in response.get_data(as_text=True)

def test_load_papers(test_client):
    response = test_client.get('/load_papers?token=test_token&n_papers=10')
    assert response.status_code == 201
