"""authorisation tests."""
# pylint: disable=redefined-outer-name. unused-argument, no-self-use

from test.conftest import EMAIL, PASS, TMP_EMAIL
from datetime import datetime, timezone, timedelta
from time import sleep

import pytest
from flask import url_for
from app.utils import encode_token, decode_token, DecodeException
from app import mail
from app.model import User, db


ROOT_LOGIN = 'auth_bp.login'
ROOT_PASSW = 'auth_bp.change_pasw'
ROOT_NEW_USER = 'auth_bp.new_user'
ROOT_EMAIL_CHANGE = 'auth_bp.email_change'
ROOT_EMAIL_CHANGE_CONF = 'auth_bp.change_email_confirm'
ROOT_LOGOUT = 'auth_bp.logout'
ROOT_VERIFY_EMAIL = 'auth_bp.verify_email_confirm'


@pytest.mark.usefixtures('live_server')
class TestAccount:
    """Test account creation and change."""
    def test_login(self, client, user):
        """Test login."""
        response = client.post(url_for(ROOT_LOGIN),
                               data={'i_login': EMAIL,
                                     'i_pass': PASS
                                     },
                               follow_redirects=True
                               )
        assert response.status_code == 200
        assert 'ERROR' not in response.get_data(as_text=True)

    def test_wrong_login(self, client):
        """Test wrong login."""
        response = client.post(url_for(ROOT_LOGIN),
                               data={'i_login': EMAIL + '1',
                                     'i_pass': PASS
                                     },
                               follow_redirects=True
                               )
        assert response.status_code == 200
        assert 'ERROR! Wrong username/password!' in response.get_data(as_text=True)

    def test_wrong_pass(self, client):
        """Test wrong login."""
        response = client.post(url_for(ROOT_LOGIN),
                               data={'i_login': EMAIL,
                                     'i_pass': PASS + '1'
                                     },
                               follow_redirects=True
                               )
        assert response.status_code == 200
        assert 'ERROR! Wrong username/password!' in response.get_data(as_text=True)

    def test_logout(self, client, login):
        """Test logout."""
        response = client.get('/logout',
                              follow_redirects=True)
        assert response.status_code == 200
        assert 'Login' in response.get_data(as_text=True)

    def test_new_acc(self, client):
        """Test new account creation."""
        response = client.post(url_for(ROOT_NEW_USER),
                               data={'email': 'tester2@mailinator.com',
                                     'pasw': 'tester2',
                                     'pasw2': 'tester2'
                                     },
                               follow_redirects=True
                               )
        assert response.status_code == 200
        assert 'ERROR' not in response.get_data(as_text=True)
        assert 'Welcome' in response.get_data(as_text=True)

    def test_new_acc_same_email(self, client, user):
        """Test new account creation with already registered email."""
        response = client.post(url_for(ROOT_NEW_USER),
                               data={'email': EMAIL,
                                     'pasw': 'tester2',
                                     'pasw2': 'tester2'
                                     },
                               follow_redirects=True
                               )
        assert response.status_code == 200
        assert 'Email is already registered' in response.get_data(as_text=True)
        assert 'Welcome' not in response.get_data(as_text=True)

    def test_new_acc_wrong_email(self, client):
        """Test new account creation with wrong email format."""
        response = client.post(url_for(ROOT_NEW_USER),
                               data={'email': 'blablabla',
                                     'pasw': 'tester2',
                                     'pasw2': 'tester2'
                                     },
                               follow_redirects=True
                               )
        assert response.status_code == 200
        assert 'The email is not correct!' in response.get_data(as_text=True)
        assert 'Welcome' not in response.get_data(as_text=True)

    def test_new_acc_diff_passw(self, client):
        """Test new account creation with different passwords."""
        response = client.post(url_for(ROOT_NEW_USER),
                               data={'email': 'tester3@mailinator.com',
                                     'pasw': 'tester2',
                                     'pasw2': 'tester3'
                                     },
                               follow_redirects=True
                               )
        assert response.status_code == 200
        assert "Passwords don't match!" in response.get_data(as_text=True)
        assert 'Welcome' not in response.get_data(as_text=True)

    def test_del_acc(self, client, tmp_login):
        """Test account delete."""
        client.post(url_for('auth_bp.login'),
                    data={'i_login': TMP_EMAIL,
                          'i_pass': PASS
                          },
                    )
        response = client.post(url_for('auth_bp.del_acc'),
                               follow_redirects=True
                               )
        assert response.status_code == 200
        assert 'Login' in response.get_data(as_text=True)


@pytest.mark.usefixtures('live_server')
class TestPassword:
    """Password related tests."""
    def test_change_pass(self, client, tmp_login):
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

    def test_unauthorised_request(self, client):
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

    def test_change_wrong_old_pass(self, client, tmp_login):
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

    def test_change_wrong_new_pass(self, client, login):
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

    def test_pass_restore(self, client, tmp_user):
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
            assert len(outbox) == 0

            response = client.post(url_for('auth_bp.restore_pass'),
                                   data={'email': TMP_EMAIL},
                                   follow_redirects=True
                                   )
            assert len(outbox) == 1
            assert outbox[0].subject == "arXiv tag password reset"
        assert 'was sent' in response.get_data(as_text=True)


@pytest.mark.usefixtures('live_server')
class TestVerificationConfirmation:
    """Test email change and verification."""
    def test_email_verification(self, client, login):
        """Test generation of the email verification email."""
        with mail.record_messages() as outbox:
            response = client.get(url_for('auth_bp.verify_email'))

            assert len(outbox) == 1
            assert outbox[0].subject == "arXiv tag email verification"

        assert response.status_code == 303

    def test_email_change_to_existing(self, client, user, tmp_login):
        """Test error throw for email change to existing user record."""
        with mail.record_messages() as outbox:
            response = client.post(url_for(ROOT_EMAIL_CHANGE),
                                   data={'newEmail': EMAIL},
                                   follow_redirects=True
                                   )
            assert len(outbox) == 0

        assert response.status_code == 200
        assert 'already registered' in response.get_data(as_text=True)

    def test_email_change_to_same(self, client, login):
        """Test error throw during attempt to change email to same one."""
        User.query.filter_by(email=EMAIL).first().verified_email = True
        db.session.commit()
        with mail.record_messages() as outbox:
            response = client.post(url_for(ROOT_EMAIL_CHANGE),
                                   data={'newEmail': EMAIL},
                                   follow_redirects=True
                                   )
            assert len(outbox) == 0

        assert response.status_code == 200
        assert 'same email' in response.get_data(as_text=True)

        User.query.filter_by(email=EMAIL).first().verified_email = False
        db.session.commit()

    def test_email_change(self, client, login):
        """Test email generation for the email change."""
        User.query.filter_by(email=EMAIL).first().verified_email = True
        db.session.commit()
        with mail.record_messages() as outbox:
            response = client.post(url_for(ROOT_EMAIL_CHANGE),
                                   data={'newEmail': TMP_EMAIL},
                                   follow_redirects=True
                                   )
            assert len(outbox) == 1
            assert outbox[0].subject == "arXiv tag email change"

        assert response.status_code == 200
        assert 'ERROR' not in response.get_data(as_text=True)
        User.query.filter_by(email=EMAIL).first().verified_email = True
        db.session.commit()

    def test_email_verification_confirmation(self, client, user):
        """Tests confirmation of email change."""
        # check that the user will be logged in with a token
        client.get(url_for(ROOT_LOGOUT))
        payload = {'email': EMAIL}
        token = encode_token(payload)
        response = client.get(url_for(ROOT_VERIFY_EMAIL,
                                      data=token),
                              follow_redirects=True
                              )
        assert response.status_code == 200
        assert 'Email verified successfully' in response.get_data(as_text=True)
        assert 'ERROR' not in response.get_data(as_text=True)

        # Client should NOT be logged in if the email was verified before
        client.get(url_for(ROOT_LOGOUT))
        response = client.get(url_for(ROOT_VERIFY_EMAIL,
                                      data=token),
                              follow_redirects=True
                              )
        assert 'Email verified successfully' not in response.get_data(as_text=True)
        assert 'ERROR' in response.get_data(as_text=True)
        assert 'Login' in response.get_data(as_text=True)

    def test_wrong_email_verification_confirmation(self, client, user):
        """Tests confirmation of email change with wrong email."""
        payload = {'email': 'tester@mailinator.com'}
        token = encode_token(payload)
        response = client.get(url_for(ROOT_VERIFY_EMAIL,
                                      data=token),
                              follow_redirects=True
                              )
        assert response.status_code == 200
        assert 'ERROR! User not found!' in response.get_data(as_text=True)

    def test_email_change_confirmation(self, client, tmp_user):
        """Tests confirmation of email verification."""
        client.get(url_for(ROOT_LOGOUT))
        payload = {'from': TMP_EMAIL,
                   'to': 'tester_wrong@mailinator.com'
                   }
        token = encode_token(payload)
        response = client.get(url_for(ROOT_EMAIL_CHANGE_CONF,
                                      data=token),
                              follow_redirects=True
                              )
        assert response.status_code == 200
        assert 'successfully' in response.get_data(as_text=True)
        assert 'ERROR' not in response.get_data(as_text=True)

    def test_wrong_old_email_change_confirmation(self, client, tmp_user):
        """Tests error during confirmation of email verification."""
        payload = {'from': 'tester@mailinator.com',
                   'to': TMP_EMAIL
                   }
        token = encode_token(payload)
        response = client.get(url_for(ROOT_EMAIL_CHANGE_CONF,
                                      data=token),
                              follow_redirects=True
                              )
        assert response.status_code == 200
        assert 'ERROR! User not found!' in response.get_data(as_text=True)

    def test_wrong_new_email_change_confirmation(self, client, tmp_user, user):
        """Tests error during confirmation of email verification."""
        payload = {'from': TMP_EMAIL,
                   'to': EMAIL
                   }
        token = encode_token(payload)
        response = client.get(url_for(ROOT_EMAIL_CHANGE_CONF,
                                      data=token),
                              follow_redirects=True
                              )
        assert response.status_code == 200
        assert 'already exists' in response.get_data(as_text=True)


@pytest.mark.usefixtures('live_server')
class TestToken:
    """JWT tests."""
    def test_good_token(self):
        """Test token encoding/decoding."""
        payload = {'new': 'very_new'}
        token = encode_token(payload)
        data = decode_token(token)
        assert 'new' in data
        assert data.get('new') == 'very_new'

    def test_token_expiration(self):
        """Test token encoding/decoding."""
        payload = {'new': 'very_new',
                   'exp': datetime.now(tz=timezone.utc) + timedelta(seconds=1)
                   }
        token = encode_token(payload)
        sleep(2)
        with pytest.raises(DecodeException):
            decode_token(token)

    def test_token_wo_keys(self):
        """Test token that has not required keys."""
        payload = {'new': 'very_new'}
        token = encode_token(payload)
        with pytest.raises(DecodeException):
            decode_token(token, keys=['to'])

    def test_invalid_token(self):
        """Test invalid token."""
        token = 'blablabla'  # nosec
        with pytest.raises(DecodeException):
            decode_token(token)
