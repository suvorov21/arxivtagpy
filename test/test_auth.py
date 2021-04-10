"""authorisation tests."""
# pylint: disable=redefined-outer-name

from werkzeug.utils import import_string
from werkzeug.security import generate_password_hash

import pytest

from app import app_init, db
from app.model import User

@pytest.fixture(scope='module', autouse=True)
def init_app():
    """Application initialisation function."""
    app = app_init()
    cfg = import_string('configmodule.TestingConfig')
    app.config.from_object(cfg)
    with app.app_context():
        db.create_all()
        testing_client = app.test_client()
        yield testing_client
        db.session.remove()
        db.drop_all()

@pytest.fixture
def create_user(init_app):
    """Create user fixture."""
    email = 'tester@gmail.com'
    user1 = User(email=email,
                 pasw=generate_password_hash('tester'),
                 arxiv_cat=['hep-ex'],
                 tags='[{"name": "test", "rule":"ti{test}", "color":"#ff0000"}]',
                 pref='{"tex": "True"}'
                 )
    db.session.add(user1)
    db.session.commit()
    yield init_app
    User.query.filter_by(email=email).delete()
    db.session.commit()

def test_general(init_app):
    """Test landing page."""
    response = init_app.get('/')
    assert response.status_code == 200

def test_log(create_user):
    """Test login."""
    response = create_user.post('/login',
                                data={'i_login': 'tester@gmail.com', 'i_pass':'tester'},
                                follow_redirects=True
                                )
    assert response.status_code == 200

def test_logout(create_user):
    """Test logout."""
    response = create_user.post('/login',
                                data={'i_login': 'tester@gmail.com', 'i_pass':'tester'},
                                follow_redirects=True
                                )

    response = create_user.get('/logout',
                               follow_redirects=True)
    assert response.status_code == 200

def test_new_acc(init_app):
    """Test new account creation."""
    response = init_app.post('/new_user',
                             data={'email': 'tester2@gmail.com',
                                   'pasw': 'tester2',
                                   'pasw2': 'tester2'
                                   },
                                   follow_redirects=True
                                   )
    assert response.status_code == 200
    assert 'ERROR' not in response.get_data(as_text=True)
    assert 'Welcome' in response.get_data(as_text=True)

def test_del_acc(create_user):
    """Test acount delete."""
    response = create_user.post('/delAcc',
                                follow_redirects=True
                                )
    assert response.status_code == 200

def test_change_pass(create_user):
    """Test password change."""
    response = create_user.post('/login',
                                data={'i_login': 'tester@gmail.com', 'i_pass':'tester'},
                                follow_redirects=True
                                )

    response = create_user.post('/change_pasw',
                                data={'oldPass': 'tester',
                                      'newPass1': 'tester_new',
                                      'newPass2': 'tester_new'
                                      },
                                follow_redirects=True
                                )
    assert response.status_code == 200
    assert 'ERROR' not in response.get_data(as_text=True)
    assert 'successfully' in response.get_data(as_text=True)

def test_unauthorised_request(init_app):
    """Test acccess to login restricted pages."""
    response = init_app.post('/change_pasw',
                             data={'oldPass': 'tester',
                                   'newPass1': 'tester_new',
                                   'newPass2': 'tester_new'
                                   },
                             follow_redirects=True
                             )
    assert response.status_code == 200
    assert 'ERROR' in response.get_data(as_text=True)

def test_change_wrong_old_pass(create_user):
    """Test login with wrong old password."""
    response = create_user.post('/login',
                                data={'i_login': 'tester@gmail.com', 'i_pass':'tester'},
                                follow_redirects=True
                                )

    response = create_user.post('/change_pasw',
                                data={'oldPass': 'tester_wrong',
                                      'newPass1': 'tester_new',
                                      'newPass2': 'tester_new'
                                      },
                                follow_redirects=True
                                )
    assert response.status_code == 200
    assert 'ERROR! Wrong' in response.get_data(as_text=True)

def test_change_wrong_new_pass(create_user):
    """Test login with wrong new password."""
    response = create_user.post('/login',
                                data={'i_login': 'tester@gmail.com', 'i_pass':'tester'},
                                follow_redirects=True
                                )
    response = create_user.post('/change_pasw',
                                data={'oldPass': 'tester',
                                      'newPass1': 'tester_new',
                                      'newPass2': 'tester_new_other'
                                      },
                                follow_redirects=True
                                )
    assert response.status_code == 200
    assert "don\'t match!" in response.get_data(as_text=True)

def test_load_papers(init_app):
    """Test paper loading."""
    response = init_app.get('/load_papers?token=test_token&n_papers=10&method=new')
    assert response.status_code == 201
