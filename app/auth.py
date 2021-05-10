"""Authority utilities: login, pass check, account managment."""

from datetime import datetime
import secrets
import string

from werkzeug.security import check_password_hash, \
generate_password_hash

from flask import Blueprint, render_template, flash, redirect, \
request, current_app
from flask_login import login_user, logout_user, \
current_user, login_required
from flask_mail import Message

from .import login_manager
from .import mail
from .model import db, User, PaperList, Tag
from .utils import url
from .settings import default_data

DEFAULT_LIST = 'Favourite'

auth_bp = Blueprint(
    'auth_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)

######### LOGIN TOOLS ##################################################


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
    email = request.form.get('i_login')
    pasw = request.form.get('i_pass')

    usr = User.query.filter_by(email=email).first()
    if not usr:
        flash('ERROR! Wrong username/password! \
              <a href="/restore" class="alert-link">Reset password?</a>')
        return redirect(url('main_bp.root'))

    if check_password_hash(usr.pasw, pasw):
        login_user(usr)
    else:
        flash('ERROR! Wrong username/password! \
              <a href="/restore" class="alert-link">Reset password?</a>')
    return redirect(url('main_bp.root'))

@auth_bp.route('/signup')
def signup():
    """Signup page."""
    return render_template('signup.jinja2')

@auth_bp.route('/logout')
@login_required
def logout():
    """User log-out logic."""
    logout_user()
    return redirect(url('main_bp.root'))

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

@auth_bp.route('/new_user', methods=["POST"])
def new_user():
    """New user creation."""
    email = request.form.get('email')
    pasw1 = request.form.get('pasw')
    pasw2 = request.form.get('pasw2')

    usr = User.query.filter_by(email=email).first()
    if usr:
        flash("ERROR! Email is already registered")
        return redirect(url('auth_bp.signup'), code=303)

    if pasw1 != pasw2:
        flash("ERROR! Passwords don't match!")
        return redirect(url('auth_bp.signup'), code=303)

    user = User(email=email,
                pasw=generate_password_hash(pasw1),
                arxiv_cat=['hep-ex'],
                created=datetime.now(),
                login=datetime.now(),
                last_paper=datetime.now(),
                pref='{"tex":"True", "theme":"light"}'
                )

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
    flash('Welcome to arXiv tag! Please setup categories you are interested in!')
    return redirect(url('settings_bp.settings_page'), code=303)

@auth_bp.route('/change_pasw', methods=["POST"])
@login_required
def change_pasw():
    """Change password."""
    old = request.form.get('oldPass')
    new = request.form.get('newPass1')
    new2 = request.form.get('newPass2')
    if new != new2:
        flash("ERROR! New passwords don't match!")
        return redirect(url('settings_bp.settings_page'))

    if not check_password_hash(current_user.pasw, old):
        flash("ERROR! Wrong old password!")
        return redirect(url('settings_bp.settings_page'))

    current_user.pasw = generate_password_hash(new)
    db.session.commit()
    flash('Password successfully changed!')
    return redirect(url('settings_bp.settings_page'), code=303)

@auth_bp.route('/delAcc', methods=["POST"])
@login_required
def del_acc():
    """Delete account completely."""
    email = current_user.email
    logout_user()
    User.query.filter_by(email=email).delete()
    db.session.commit()

    return redirect(url('main_bp.root'), code=303)

@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to Login page."""
    flash('ERROR! You must be logged in to view this page.')
    return redirect(url('main_bp.about'))

@auth_bp.route('/restore', methods=['GET'])
def restore():
    """Page for password reset."""
    return render_template('restore.jinja2',
                           data=default_data()
                           )

@auth_bp.route('/restore_pass', methods=['POST'])
def restore_pass():
    """Endpoint for password reset."""
    do_send = request.args.get('do_send')
    email_in = request.form.get('email')
    user = User.query.filter_by(email=email_in).first()
    if user:
        # generate new pass
        letters = string.ascii_letters + string.digits
        new_pass = ''.join(secrets.choice(letters) for i in range(15)) # nosec
        user.pasw = generate_password_hash(new_pass)
        db.session.commit()

        # create an email
        body = 'Hello,\n\nYour password for the website arxivtag.tk'
        body += ' was reset. The new password is provided below.\n'
        body += 'Please, consider password change immidietly after login'
        body += ' at the settings page.'
        body += '\n\nNew password:\n' + new_pass
        body += '\n\nRegards, \narXiv tag team.'
        msg = Message(body=body,
                      sender="noreply@arxivtag.tk",
                      recipients=[user.email],
                      subject="arXiv tag password reset"
                      )
        if do_send:
            mail.send(msg)

    flash(f'The email with a new password was sent to your email from \
          {current_app.config["MAIL_DEFAULT_SENDER"]}')
    return redirect(url('main_bp.root'), code=303)