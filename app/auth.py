"""Authority utilities: login, pass check, account managment."""

from datetime import datetime, timezone, timedelta
import secrets
import string
import logging
import re
import requests

from werkzeug.security import check_password_hash, \
    generate_password_hash

from flask import Blueprint, render_template, flash, redirect, \
    request, current_app, url_for
from flask_login import login_user, logout_user, \
    current_user, login_required
from flask_mail import Message

from .import login_manager

from .model import db, User, PaperList, Tag
from .utils import encode_token, decode_token, DecodeException
from .utils_app import mail_catch
from .settings import default_data

DEFAULT_LIST = 'Favourite'

auth_bp = Blueprint(
    'auth_bp',
    __name__,
    template_folder='templates',
    static_folder='frontend'
)

ROOT_PATH = 'main_bp.root'
SIGNUP_ROOT = 'auth_bp.signup'
ROOT_SET = 'settings_bp.settings_page'


@login_manager.user_loader
def load_user(user_id):
    """Load user function, store username."""
    if user_id is not None:
        usr = User.query.get(user_id)
        return usr
    return None


@auth_bp.route('/login', methods=['POST'])
def login():
    """User log-in logic."""
    email = request.form.get('i_login').lower()
    pasw = request.form.get('i_pass')

    usr = User.query.filter_by(email=email).first()
    if not usr:
        flash('ERROR! Wrong username/password! \
              <a href="/restore" class="alert-link">Reset password?</a>')
        return redirect(url_for(ROOT_PATH))

    if check_password_hash(usr.pasw, pasw):
        login_user(usr)
    else:
        flash('ERROR! Wrong username/password! \
              <a href="/restore" class="alert-link">Reset password?</a>')
    return redirect(url_for(ROOT_PATH))


@auth_bp.route('/signup')
def signup():
    """Signup page."""
    return render_template('signup.jinja2',
                           data=default_data()
                           )


@auth_bp.route('/logout')
@login_required
def logout():
    """User log-out logic."""
    logout_user()
    return redirect(url_for(ROOT_PATH))


def new_default_list(usr_id):
    """Create default paper list for a given user."""
    result = PaperList.query.filter_by(user_id=usr_id,
                                       name=DEFAULT_LIST
                                       ).first()
    if result:
        return

    paper_list = PaperList(name=DEFAULT_LIST,
                           user_id=usr_id,
                           not_seen=0
                           )
    db.session.add(paper_list)

    db.session.commit()


def new_user_routine(user: User):
    """Create and add default tag to user."""
    tag = Tag(name='example',
              rule='abs{physics|math}',
              color='#fff2bd',
              order=0,
              public=False,
              email=False,
              bookmark=False
              )
    user.tags.append(tag)
    db.session.add(user)
    db.session.commit()

    new_default_list(user.id)

    login_user(user)
    message = 'Welcome to arXiv tag! Please setup rules to classify papers.<br>'
    message += '1. To check the syntax click on "Show rules hints"<br>'
    message += '2. To see example from other users click on "Show users rules examples."<br>'
    message += 'You can modify the settings later at any time.'
    flash(message)
    return redirect(url_for(ROOT_SET, page='tag'), code=303)


@auth_bp.route('/new_user', methods=["POST"])
def new_user():
    """New user creation."""
    email = request.form.get('email').lower()
    pasw1 = request.form.get('pasw')
    pasw2 = request.form.get('pasw2')

    usr = User.query.filter_by(email=email).first()
    if usr:
        flash("ERROR! Email is already registered")
        return redirect(url_for(SIGNUP_ROOT), code=303)

    if pasw1 != pasw2:
        flash("ERROR! Passwords don't match!")
        return redirect(url_for(SIGNUP_ROOT), code=303)

    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if not re.fullmatch(regex, email):
        flash("ERROR! The email is not correct!")
        return redirect(url_for(SIGNUP_ROOT), code=303)

    user = User(email=email,
                verified_email=False,
                pasw=generate_password_hash(pasw1),
                arxiv_cat=['hep-ex'],
                created=datetime.now(),
                login=datetime.now(),
                last_paper=datetime.now(),
                pref='{"tex":"True", "theme":"light"}',
                recent_visit=0
                )

    return new_user_routine(user)


@auth_bp.route('/change_pasw', methods=["POST"])
@login_required
def change_pasw():
    """Change password."""
    old = request.form.get('oldPass')
    new = request.form.get('newPass1')
    new2 = request.form.get('newPass2')
    if new != new2:
        flash("ERROR! New passwords don't match!")
        return redirect(url_for(ROOT_SET, page='pref'))

    # check for the old password only if any (3rd party OAth may be used)
    if current_user.pasw:
        if not check_password_hash(current_user.pasw, old):
            flash("ERROR! Wrong old password!")
            return redirect(url_for(ROOT_SET, page='pref'))

    current_user.pasw = generate_password_hash(new)
    db.session.commit()
    flash('Password successfully changed!')
    return redirect(url_for(ROOT_SET, page='pref'), code=303)


@auth_bp.route('/delAcc', methods=["POST"])
@login_required
def del_acc():
    """Delete account completely."""
    email = current_user.email
    logout_user()
    User.query.filter_by(email=email).delete()
    db.session.commit()

    flash("Account is successfully deleted!")

    return redirect(url_for(ROOT_PATH), code=303)


@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to Login page."""
    flash('ERROR! You must be logged in to view this page.')
    return redirect(url_for('main_bp.about'))


@auth_bp.route('/restore', methods=['GET'])
def restore():
    """Page for password reset."""
    return render_template('restore.jinja2',
                           data=default_data()
                           )


@auth_bp.route('/restore_pass', methods=['POST'])
def restore_pass():
    """Endpoint for password reset."""
    email_in = request.form.get('email').lower()
    user = User.query.filter_by(email=email_in).first()
    # Success will go to False ONLY if the user IS found
    # but the problem during email sending happens
    success = True
    if user:
        # generate new pass
        letters = string.ascii_letters + string.digits
        new_pass = ''.join(secrets.choice(letters) for _ in range(15))  # nosec
        user.pasw = generate_password_hash(new_pass)
        db.session.commit()

        # create an email
        body = 'Hello,\n\nYour password for the website' + request.headers['Host']
        body += ' was reset. The new password is provided below.\n'
        body += 'Please, consider password change immediately after login'
        body += ' at the settings page.'
        body += '\n\nNew password:\n' + new_pass
        body += '\n\nRegards, \narXiv tag team.'

        html = render_template('mail_pass.jinja2',
                               host=request.headers['Host'],
                               pasw=new_pass
                               )
        msg = Message(body=body,
                      html=html,
                      sender=current_app.config['MAIL_DEFAULT_SENDER'],
                      recipients=[user.email],
                      subject="arXiv tag password reset"
                      )
        success = mail_catch(msg)

    if success:
        flash(f'The email with a new password was sent to your email from \
              <span class="font-weight-bold"> \
              {current_app.config["MAIL_DEFAULT_SENDER"]} \
              </span>. <br /> Check spam folder in case no email is received.')
        logging.info('Successful password recovery.')
    else:
        logging.error('Error sending email with pass recovery')
        flash('ERROR! Server experienced an internal error. We are working on fix. \
              Please, try later')
    return redirect(url_for(ROOT_PATH), code=303)


@auth_bp.route('/oath', methods=['GET'])
def oath():
    """Authentication with ORCID API."""
    code = request.args.get('code')
    headers = {'Accept': 'application/json'}
    data = {'client_id': 'APP-CUS94SZ4NVHZ1IFS',
            'client_secret': 'c73364d5-2602-43a5-a9c5-e0a50033243e',
            'grant_type': 'authorization_code',
            # TODO upate with HTTPS
            'redirect_uri': 'http://' + request.headers['Host'] + '/oath',
            'code': str(code)
            }

    # Because of some black magic requests.post() is not working,
    # and we have to use requests.Request()
    # The possible reason is some additional headers requests adds to POST by default.
    # response = requests.post('https://sandbox.orcid.org/oauth/token',
    #                          headers=headers,
    #                          data=data)
    # print(response.headers)

    req = requests.Request('POST',
                           f'{current_app.config["ORCID_URL"]}/oauth/token',
                           data=data,
                           headers=headers
                           )
    prepared = req.prepare()
    req_session = requests.Session()
    response = req_session.send(prepared)

    if response.status_code != 200 or 'orcid' not in response.json():
        logging.error('Error with ORCID OAth. Code %i', response.status_code)
        message = 'ERROR! ORCID respond with error.<br>'
        message += 'We are notified and investigating the problem.<br>'
        message += 'You can try login with email/password.'
        flash(message)
        return redirect(url_for(ROOT_PATH), code=303)

    user = User.query.filter_by(orcid=response.json()['orcid']).first()

    if not user:
        # ORCID record is not found, but current user is authenticated
        # add ORCID to his record
        if current_user and current_user.is_authenticated:
            current_user.orcid = response.json()['orcid']
            db.session.commit()
            flash('ORCID linked successfully')
            return redirect(url_for(ROOT_SET, page='pref'), code=303)
        # if no current_user --> create a new one
        user = User(orcid=response.json()['orcid'],
                    arxiv_cat=['hep-ex'],
                    created=datetime.now(),
                    login=datetime.now(),
                    last_paper=datetime.now(),
                    pref='{"tex":"True", "theme":"light"}',
                    recent_visit=0,
                    verified_email=False
                    )

        return new_user_routine(user)

    # ORCID record is found, but user is authenticated
    # throw an error as ORCID num is unique in users table
    if current_user and current_user.is_authenticated:
        flash('ERROR! User with this orcid is already registered!')
        return redirect(url_for(ROOT_PATH), code=303)
    # if no current_user, but ORCID record is in the DB --> authenticate
    login_user(user)

    return redirect(url_for(ROOT_PATH), code=303)


@auth_bp.route('/email_change', methods=['POST'])
@login_required
def email_change():
    """Change email for the current user."""
    new = request.form.get('newEmail')
    if not current_user.email:
        current_user.email = new
        db.session.commit()
        message = 'Email changed successfully! You can verify it now.'
        flash(message)
        return redirect(url_for(ROOT_SET, page='pref'), code=303)

    user = User.query.filter_by(email=new).first()
    if user:
        flash("ERROR! User with new email is already registered.")
        return redirect(url_for(ROOT_SET, page='pref'), code=303)

    payload = {'exp': datetime.now(tz=timezone.utc) + timedelta(days=1),
               'from': current_user.email,
               'to': new}
    token = encode_token(payload)

    # create an email
    body = 'Hello,\n\nYour email in the account at the website' + request.headers['Host']
    body += f'was requested to be changed to {new}.\n'
    body += 'If it was not you - ignore the message.'
    body += ' If you are sure you want to change the email use the link below\n\n'
    body += f'http://{request.headers["Host"]}/change_email_confirm?data={token}'

    html = render_template('mail_email_change.jinja2',
                           host=request.headers['Host'],
                           new_emal=new,
                           href=f'http://{request.headers["Host"]}/change_email_confirm?data={token}'
                           )
    msg = Message(body=body,
                  html=html,
                  sender=current_app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[current_user.email],
                  subject="arXiv tag email change"
                  )

    success = mail_catch(msg)

    message = 'ERROR! Confirmation email is not send. Please try later.'
    if success:
        message = f'Email with confirmation link was sent to your email {current_user.email}'
        message += '<br>Until confirmation, the old email will be used.'
    else:
        logging.error('Error while sending email change confirmation')

    flash(message)
    return redirect(url_for(ROOT_SET, page='pref'), code=303)


@auth_bp.route('/verify_email', methods=['GET'])
@login_required
def verify_email():
    """Verify email for the current user."""
    if not current_user.email:
        flash('ERROR! No email is registered for your account!')
        return redirect(url_for(ROOT_SET, page='pref'), code=303)

    payload = {'exp': datetime.now(tz=timezone.utc) + timedelta(days=1),
               'email': current_user.email
               }
    token = encode_token(payload)
    href = f'http://{request.headers["Host"]}/verify_email_confirm?data={token}'

    # create an email
    body = 'Hello,\n\nplease verify your email for the website' + request.headers['Host']
    body += '\n with the link below\n\n'
    body += href

    html = render_template('mail_email_verification.jinja2',
                           host=request.headers['Host'],
                           href=href
                           )
    msg = Message(body=body,
                  html=html,
                  sender=current_app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[current_user.email],
                  subject="arXiv tag email verification"
                  )

    success = mail_catch(msg)

    message = 'ERROR! Confirmation email is not send. Please try later.'
    if success:
        message = f'Email with confirmation link was sent to your email {current_user.email}'
    else:
        logging.error('Error while sending email verification')

    flash(message)
    return redirect(url_for(ROOT_SET, page='pref'), code=303)


@auth_bp.route('/change_email_confirm', methods=['GET'])
def change_email_confirm():
    """Hook for email changing confirmation."""
    token = request.args.get('data')
    try:
        decoded = decode_token(token, keys=['to', 'from'])
    except DecodeException:
        return redirect(url_for(ROOT_SET, page='pref'), code=303)

    user = User.query.filter_by(email=decoded['from']).first()
    if not user:
        logging.error('User not found during email change')
        flash('ERROR! User not found!')
        return redirect(url_for(ROOT_SET, page='pref'), code=303)

    user_tmp = User.query.filter_by(email=decoded['to']).first()
    if user_tmp:
        flash('ERROR! User with entered email already exists!')
        return redirect(url_for(ROOT_SET, page='pref'), code=303)

    user.email = decoded['to']
    user.verified_email = False
    db.session.commit()

    flash('Email changed successfully!')
    return redirect(url_for(ROOT_SET, page='pref'), code=303)


@auth_bp.route('/verify_email_confirm', methods=['GET'])
def verify_email_confirm():
    """Verification of the email with token."""
    token = request.args.get('data')
    try:
        decoded = decode_token(token, keys=['email'])
    except DecodeException:
        return redirect(url_for(ROOT_SET, page='pref'), code=303)

    user = User.query.filter_by(email=decoded.get('email')).first()
    if not user:
        logging.error('User not found during email verification')
        flash('ERROR! User not found!')
        return redirect(url_for(ROOT_SET, page='pref'), code=303)

    user.verified_email = True
    db.session.commit()

    flash('Email verified successfully!')
    return redirect(url_for(ROOT_SET, page='pref'), code=303)


@auth_bp.route('/orcid', methods=['GET'])
def orcid():
    """Redirect to ORCID authentication page."""
    # if user exists and authenticated
    if current_user and current_user.is_authenticated:
        # if ORCID is already linked -> unlink ORCID
        if current_user.orcid:
            # check if alternative authentication is available
            if not current_user.email or not current_user.pasw:
                flash('ERROR! Could not unlink ORCID this is your only authentication method')
                return redirect(url_for(ROOT_SET, page='pref'), code=303)

            # unlink orcid
            current_user.orcid = None
            db.session.commit()
            flash('ORCID unlinked successfully')
            return redirect(url_for(ROOT_SET, page='pref'), code=303)

    href = '{}{}{}{}{}{}'.format(current_app.config['ORCID_URL'],
                                 '/oauth/authorize?client_id=',
                                 current_app.config['ORCID_APP'],
                                 '&response_type=code&scope=/authenticate',
                                 '&redirect_uri=',
                                 # TODO UPDATE with HTTPS
                                 'http://' + request.headers['Host'] + '/oath'
                                 )
    return redirect(href, code=303)
