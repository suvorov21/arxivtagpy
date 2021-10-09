"""authorisation tests."""
# pylint: disable=redefined-outer-name. unused-argument

from test.conftest import EMAIL, PASS

from flask import url_for

ROOT_LOGIN = 'auth_bp.login'
ROOT_PASSW = 'auth_bp.change_pasw'


def test_general(client):
    """Test landing page."""
    response = client.get(url_for('main_bp.root'))
    assert response.status_code == 200


def test_login(client):
    """Test login."""
    response = client.post(url_for(ROOT_LOGIN),
                           data={'i_login': EMAIL,
                                 'i_pass': PASS
                                 },
                           follow_redirects=True
                           )
    assert response.status_code == 200
    assert 'ERROR' not in response.get_data(as_text=True)


def test_wrong_login(client):
    """Test wrong login."""
    response = client.post(url_for(ROOT_LOGIN),
                           data={'i_login': EMAIL + '1',
                                 'i_pass': PASS
                                 },
                           follow_redirects=True
                           )
    assert response.status_code == 200
    assert 'ERROR! Wrong username/password!' in response.get_data(as_text=True)


def test_wrong_pass(client):
    """Test wrong login."""
    response = client.post(url_for(ROOT_LOGIN),
                           data={'i_login': EMAIL,
                                 'i_pass': PASS + '1'
                                 },
                           follow_redirects=True
                           )
    assert response.status_code == 200
    assert 'ERROR! Wrong username/password!' in response.get_data(as_text=True)


def test_logout(client, login):
    """Test logout."""
    response = client.get('/logout',
                          follow_redirects=True)
    assert response.status_code == 200
    assert 'Login' in response.get_data(as_text=True)


def test_new_acc(client):
    """Test new account creation."""
    response = client.post('/new_user',
                           data={'email': 'tester2@gmail.com',
                                 'pasw': 'tester2',
                                 'pasw2': 'tester2'
                                 },
                           follow_redirects=True
                           )
    assert response.status_code == 200
    assert 'ERROR' not in response.get_data(as_text=True)
    assert 'Welcome' in response.get_data(as_text=True)


def test_del_acc(client, tmp_user):
    """Test account delete."""
    response = client.post('/delAcc',
                           follow_redirects=True
                           )
    assert response.status_code == 200
    assert 'Login' in response.get_data(as_text=True)


def test_change_pass(client, tmp_user):
    """Test password change."""
    response = client.post(url_for(ROOT_PASSW),
                           data={'oldPass': PASS,
                                 'newPass1': 'tester_new',
                                 'newPass2': 'tester_new'
                                 },
                           follow_redirects=True
                           )
    assert response.status_code == 200
    assert 'ERROR' not in response.get_data(as_text=True)
    assert 'successfully' in response.get_data(as_text=True)


def test_unauthorised_request(client):
    """Test acccess to login restricted pages."""
    response = client.post(url_for(ROOT_PASSW),
                           data={'oldPass': PASS,
                                 'newPass1': 'tester_new',
                                 'newPass2': 'tester_new'
                                 },
                           follow_redirects=True
                           )
    assert response.status_code == 200
    assert 'ERROR! You must be logged in' in response.get_data(as_text=True)


def test_change_wrong_old_pass(client, tmp_user):
    """Test login with wrong old password."""
    response = client.post(url_for(ROOT_PASSW),
                           data={'oldPass': 'tester_wrong',
                                 'newPass1': 'tester_new',
                                 'newPass2': 'tester_new'
                                 },
                           follow_redirects=True
                           )
    assert response.status_code == 200
    assert 'ERROR! Wrong' in response.get_data(as_text=True)


def test_change_wrong_new_pass(client, login):
    """Test login with wrong new password."""
    response = client.post(url_for(ROOT_PASSW),
                           data={'oldPass': PASS,
                                 'newPass1': 'tester_new',
                                 'newPass2': 'tester_new_other'
                                 },
                           follow_redirects=True
                           )
    assert response.status_code == 200
    assert "don\'t match!" in response.get_data(as_text=True)


def test_pass_restore(client):
    """Test password restore."""
    client.post('/new_user',
                data={'email': 'tester3@gmail.com',
                      'pasw': 'tester2',
                      'pasw2': 'tester2'
                      },
                follow_redirects=True
                )
    client.get('/logout',
               follow_redirects=True)
    response = client.post(url_for('auth_bp.restore_pass'),
                           data={'email': 'tester3@gmail.com',
                                 'do_send': 'False'
                                 },
                           follow_redirects=True
                           )
    assert 'was sent' in response.get_data(as_text=True)
