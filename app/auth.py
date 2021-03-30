from datetime import datetime

from flask import Blueprint, render_template, flash, redirect, \
url_for, request
from flask_login import login_user, logout_user, \
current_user, login_required

from werkzeug.security import check_password_hash, \
generate_password_hash

from .import login_manager
from .model import db, User

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
        flash("Wrong username/password")
        return redirect(url_for('main_bp.root'))

    if check_password_hash(usr.pasw, pasw):
        login_user(usr)
    else:
        flash("Wrong username/password")
    return redirect(url_for('main_bp.root'))

@auth_bp.route('/signup')
def signup():
    """Signup page."""
    return render_template('signup.jinja2')

@auth_bp.route('/logout')
@login_required
def logout():
    """User log-out logic."""
    logout_user()
    return redirect(url_for('main_bp.root'))

@auth_bp.route('/new_user', methods=["POST"])
def new_user():
    """New user creation."""
    email = request.form.get('email')
    pasw1 = request.form.get('pasw')
    pasw2 = request.form.get('pasw2')

    usr = User.query.filter_by(email=email).first()
    if usr:
        flash("Email is already registered")
        return redirect(url_for('main_bp.signup'))

    if pasw1 != pasw2:
        flash("Passwords don't match!")
        return redirect(url_for('main_bp.signup'))

    user = User(email=email,
                pasw=generate_password_hash(pasw1),
                arxiv_cat=['hep-ex'],
                created=datetime.now(),
                login=datetime.now(),
                last_paper=datetime.now(),
                tags='[]',
                pref='{"tex":"True", "easy_and":"True"}'
                )
    db.session.add(user)
    db.session.commit()
    login_user(user)
    flash('Welcome to arXiv tag! Please setup categories you are interested in!')
    return redirect(url_for('main_bp.settings'))

@auth_bp.route('/change_pasw', methods=["POST"])
@login_required
def change_pasw():
    """Change password."""
    old = request.form.get('oldPass')
    new = request.form.get('newPass1')
    new2 = request.form.get('newPass2')
    if new != new2:
        flash("New passwords don't match!")
        return redirect(url_for('main_bp.settings'))

    if not check_password_hash(current_user.pasw, old):
        flash("Wrong old password!")
        return redirect(url_for('main_bp.settings'))

    current_user.pasw = generate_password_hash(new)
    db.session.commit()
    flash('Password successfully changed!')
    return redirect(url_for('main_bp.settings'))

@auth_bp.route('/delAcc', methods=["POST"])
@login_required
def del_acc():
    """Delete account completely."""
    email = current_user.email
    logout_user()
    User.query.filter_by(email=email).delete()
    db.session.commit()
    return redirect(url_for('main_bp.root'))

@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to Login page."""
    flash('You must be logged in to view this page.')
    return redirect(url_for('main_bp.about'))