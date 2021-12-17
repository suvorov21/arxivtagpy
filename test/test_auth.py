"""authorisation tests."""
# pylint: disable=redefined-outer-name. unused-argument

from test.conftest import EMAIL, PASS, TMP_EMAIL
from datetime import datetime, timezone, timedelta
from time import sleep

from flask import url_for
from app.utils import encode_token, decode_token, DecodeException
from app import mail

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
                           data={'email': 'tester2@mailinator.com',
                                 'pasw': 'tester2',
                                 'pasw2': 'tester2'
                                 },
                           follow_redirects=True
                           )
    assert response.status_code == 200
    assert 'ERROR' not in response.get_data(as_text=True)
    assert 'Welcome' in response.get_data(as_text=True)


def test_new_acc_same_email(client):
    """Test new account creation with already registered email."""
    response = client.post('/new_user',
                           data={'email': 'tester2@mailinator.com',
                                 'pasw': 'tester2',
                                 'pasw2': 'tester2'
                                 },
                           follow_redirects=True
                           )
    assert response.status_code == 200
    assert 'Email is already registered' in response.get_data(as_text=True)
    assert 'Welcome' not in response.get_data(as_text=True)


def test_new_acc_wrong_email(client):
    """Test new account creation with wrong email format."""
    response = client.post('/new_user',
                           data={'email': 'blablabla',
                                 'pasw': 'tester2',
                                 'pasw2': 'tester2'
                                 },
                           follow_redirects=True
                           )
    assert response.status_code == 200
    assert 'The email is not correct!' in response.get_data(as_text=True)
    assert 'Welcome' not in response.get_data(as_text=True)


def test_new_acc_diff_passw(client):
    """Test new account creation with different passwords."""
    response = client.post('/new_user',
                           data={'email': 'tester3@mailinator.com',
                                 'pasw': 'tester2',
                                 'pasw2': 'tester3'
                                 },
                           follow_redirects=True
                           )
    assert response.status_code == 200
    assert "Passwords don't match!" in response.get_data(as_text=True)
    assert 'Welcome' not in response.get_data(as_text=True)


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
    """Test access to login restricted pages."""
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


def test_email_verification(client, login):
    """Test generation of the email verification email."""
    with mail.record_messages() as outbox:
        response = client.get(url_for('auth_bp.verify_email'))

        assert len(outbox) == 1
        assert outbox[0].subject == "arXiv tag email verification"

    assert response.status_code == 303


def test_email_change_to_existing(client, login, tmp_user):
    """Test error throw for email change to existing user record."""
    with mail.record_messages() as outbox:
        response = client.post(url_for('auth_bp.email_change'),
                               data={'newEmail': EMAIL},
                               follow_redirects=True
                               )
        assert len(outbox) == 0

    assert response.status_code == 200
    assert 'already registered' in response.get_data(as_text=True)


def test_email_change_to_same(client, login):
    """Test error throw during attempt to change email to same one."""
    with mail.record_messages() as outbox:
        response = client.post(url_for('auth_bp.email_change'),
                               data={'newEmail': EMAIL},
                               follow_redirects=True
                               )
        assert len(outbox) == 0

    assert response.status_code == 200
    assert 'same email' in response.get_data(as_text=True)


def test_email_change(client, login):
    """Test email generation for the email change."""
    with mail.record_messages() as outbox:
        response = client.post(url_for('auth_bp.email_change'),
                               data={'newEmail': TMP_EMAIL},
                               follow_redirects=True
                               )
        assert len(outbox) == 1
        assert outbox[0].subject == "arXiv tag email change"

    assert response.status_code == 200
    assert 'ERROR' not in response.get_data(as_text=True)


def test_email_verification_confirmation(client):
    """Tests confirmation of email change."""
    payload = {'email': EMAIL}
    token = encode_token(payload)
    response = client.get(url_for('auth_bp.verify_email_confirm',
                                  data=token),
                          follow_redirects=True
                          )
    assert response.status_code == 200
    assert 'successfully' in response.get_data(as_text=True)


def test_wrong_email_verification_confirmation(client):
    """Tests confirmation of email change with wrong email."""
    payload = {'email': 'tester@mailinator.com'}
    token = encode_token(payload)
    response = client.get(url_for('auth_bp.verify_email_confirm',
                                  data=token),
                          follow_redirects=True
                          )
    assert response.status_code == 200
    assert 'ERROR! User not found!' in response.get_data(as_text=True)


def test_email_change_confirmation(client, tmp_user):
    """Tests confirmation of email verification."""
    payload = {'from': TMP_EMAIL,
               'to': 'tester_wrong@mailinator.com'
               }
    token = encode_token(payload)
    response = client.get(url_for('auth_bp.change_email_confirm',
                                  data=token),
                          follow_redirects=True
                          )
    assert response.status_code == 200
    assert 'successfully' in response.get_data(as_text=True)


def test_wrong_old_email_change_confirmation(client, tmp_user):
    """Tests error during confirmation of email verification."""
    payload = {'from': 'tester@mailinator.com',
               'to': TMP_EMAIL
               }
    token = encode_token(payload)
    response = client.get(url_for('auth_bp.change_email_confirm',
                                  data=token),
                          follow_redirects=True
                          )
    assert response.status_code == 200
    assert 'ERROR! User not found!' in response.get_data(as_text=True)


def test_wrong_new_email_change_confirmation(client, tmp_user):
    """Tests error during confirmation of email verification."""
    payload = {'from': TMP_EMAIL,
               'to': EMAIL
               }
    token = encode_token(payload)
    response = client.get(url_for('auth_bp.change_email_confirm',
                                  data=token),
                          follow_redirects=True
                          )
    assert response.status_code == 200
    assert 'already exists' in response.get_data(as_text=True)


def test_pass_restore(client, tmp_user):
    """Test password restore."""
    with mail.record_messages() as outbox:
        # The email is sent ONLY if the user is registered!
        # But the message "email was sent" is shown always
        # for privacy reasons
        response = client.post(url_for('auth_bp.restore_pass'),
                               data={'email': 'tester3@mailinator.com'},
                               follow_redirects=True
                               )
        assert response.status_code == 200
        assert 'was sent' in response.get_data(as_text=True)

        response = client.post(url_for('auth_bp.restore_pass'),
                               data={'email': TMP_EMAIL},
                               follow_redirects=True
                               )
        assert len(outbox) == 1
        assert outbox[0].subject == "arXiv tag password reset"
    assert 'was sent' in response.get_data(as_text=True)


def test_good_token():
    """Test token encoding/decoding."""
    payload = {'new': 'very_new'}
    token = encode_token(payload)
    data = decode_token(token)
    assert 'new' in data
    assert data.get('new') == 'very_new'


def test_token_expiration():
    """Test token encoding/decoding."""
    payload = {'new': 'very_new',
               'exp': datetime.now(tz=timezone.utc) + timedelta(seconds=1)
               }
    token = encode_token(payload)
    sleep(2)
    try:
        decode_token(token)
        assert False
    except DecodeException:
        assert True


def test_token_wo_keys():
    """Test token that has not required keys."""
    payload = {'new': 'very_new'}
    token = encode_token(payload)
    try:
        decode_token(token, keys=['to'])
        assert False
    except DecodeException:
        assert True
