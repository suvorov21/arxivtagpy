# from datetime import datetime
from json import loads

from flask import Blueprint, render_template, flash, session, redirect, \
url_for, request, jsonify
from flask_login import current_user, login_user, login_required, logout_user

from werkzeug.security import check_password_hash, generate_password_hash

from .import login_manager
from .model import db, User
from .render import render_papers, render_title
from .papers import ArxivApi, process_papers

main_bp = Blueprint(
    'main_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)

@main_bp.route('/')
def root():
    """Landing page."""
    return render_template('layout.jinja2')

@main_bp.route('/papers')
@login_required
def papers_list():
    """Papers list page."""
    date_dict = {'today': 0,
                 'week': 1,
                 'month': 2,
                 'last': 3
                 }

    date_type = None
    if 'date' in request.args:
        date_type = date_dict.get(request.args['date'])

    if date_type is None:
        return redirect(url_for('main_bp.papers_list', date='today'))

    # load preferences
    load_prefs()

    # get rid of tag rule at front-end
    tags_dict = [{'color': tag['color'],
                  'name': tag['name']
                  } for num, tag in enumerate(session['tags'])]

    return render_template('papers.jinja2',
                           title=render_title(date_type),
                           cats=session['cats'],
                           tags=tags_dict,
                           math_jax=True
                           )

@main_bp.route('/data')
@login_required
def data():
    """API for paper download and process."""
    date_dict = {'today': 0,
                 'week': 1,
                 'month': 2,
                 'last': 3
                 }

    date_type = None
    if 'date' in request.args:
        date_type = date_dict.get(request.args['date'])

    # define an arXiv API with the categories of interest
    if 'cats' not in session:
        session['cats'] = current_user.arxiv_cat
    cats_query = r'%20OR%20'.join(f'cat:{cat}' for cat in session['cats'])
    paper_api = ArxivApi({'search_query': cats_query}#,
                         # TODO
                         # last_paper=current_user.last_paper
                         )
    # further code is paper source independent.
    # Any API can be defined above
    if 'tags' not in session:
        session['tags'] = loads(current_user.tags)
    papers = paper_api.get_papers(date_type)

    # store the info about last checked paper
    # descending paper order is assumed
    if date_type == 3:
      # TODO
        last_paper = papers['content'][0].date_up

    papers = process_papers(papers,
                            session['tags'],
                            session['cats']
                            )
    paper_render = render_papers(papers)

    content = {'papers': paper_render,
               'ncat': papers['n_cats'],
               'ntag': papers['n_tags'],
               'nnov': papers['n_nov']
               }
    return jsonify(content)

@main_bp.route('/bookshelf')
@login_required
def bookshelf():
    """Bookshelf page."""
    return render_template('bookshelf.jinja2')

@main_bp.route('/settings')
@login_required
def settings():
    """Settings page."""
    load_prefs()
    return render_template('settings.jinja2',
                           cats=session['cats'],
                           tags=session['tags'])

@main_bp.route('/about')
@login_required
def about():
    """About page."""
    return render_template('about.jinja2')


def load_prefs():
    """Load preferences from DB to session."""
    if 'cats' not in session:
        session['cats'] = current_user.arxiv_cat

    # read tags
    if 'tags' not in session:
        session['tags'] = loads(current_user.tags)


@main_bp.route('/add_cat', methods=['POST'])
@login_required
def add_cat():
    new_cat = request.form.get('cat_name')
    return new_cat


@login_manager.user_loader
def load_user(user_id):
    """Load user function, store username."""
    if user_id is not None:
        usr = User.query.get(user_id)
        # usr.login = datetime.now()
        # db.session.commit()
        return usr
    return None

@main_bp.route('/login', methods=['POST'])
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

@main_bp.route('/signup')
def signup():
    """Signup page."""
    return render_template('signup.jinja2')

@main_bp.route('/logout')
@login_required
def logout():
    """User log-out logic."""
    logout_user()
    return redirect(url_for('main_bp.root'))

@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to Login page."""
    flash('You must be logged in to view that page.')
    return redirect(url_for('main_bp.root'))
