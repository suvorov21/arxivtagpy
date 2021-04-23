"""Main blueprint with all the main pages."""

from datetime import datetime, timedelta
from json import dumps
import logging

from flask import Blueprint, render_template, session, redirect, \
request, jsonify, current_app
from flask_login import current_user, login_required
# from flask_mail import Message

from .model import db, Paper, PaperList, paper_associate
from .render import render_papers, render_title
from .auth import new_default_list, DEFAULT_LIST
from .papers import update_papers, process_papers, render_paper_json
from .paper_api import ArxivOaiApi, get_arxiv_last_date
from .utils import url
from .settings import load_prefs
# from . import mail

main_bp = Blueprint(
    'main_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)

########### MAIN PAGES #################################################

@main_bp.route('/')
def root():
    """Landing page."""
    load_prefs()
    dark = session.get('pref') and session['pref'].get('dark')
    return render_template('about.jinja2',
                           dark=dark
                           )

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
        return redirect(url('main_bp.papers_list', date='today'))


    # load preferences
    load_prefs()

    # get rid of tag rule at front-end
    tags_dict = [{'color': tag['color'],
                  'name': tag['name']
                  } for tag in session['tags']]

    return render_template('papers.jinja2',
                           title=render_title(date_type, current_user.login),
                           cats=session['cats'],
                           tags=tags_dict,
                           math_jax=session['pref'].get('tex'),
                           dark=session['pref'].get('dark')
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

    if 'date' in request.args:
        date_type = date_dict.get(request.args['date'])
    else:
        logging.error('Wrong data format')
        return dumps({'success': False}), 422

    last_paper = Paper.query.order_by(Paper.date_up.desc()).first()
    if not last_paper:
        logging.error('Paper table is empty')
        return dumps({'success': False}), 422

    today_date = last_paper.date_up

    old_date = current_user.last_paper
    old_date = get_arxiv_last_date(today_date, old_date, date_type)

    papers = {'n_cats': None,
              'n_nov': None,
              'n_tags': None,
              'last_date': old_date,
              'papers': []
              }

    # define categories of interest
    load_prefs()
    paper_query = Paper.query.filter(Paper.cats.overlap(session['cats']),
                                     Paper.date_up > old_date
                                     ).all()
    for paper in paper_query:
        papers['papers'].append(render_paper_json(paper))

    # error hahdler
    if len(papers['papers']) == 0:
        # TODO check the agreement with JS error handler
        logging.warning('No papers suitable with request')
        return jsonify(papers)

    # store the info about last checked paper
    # descending paper order is assumed
    # TODO checkl the logic. If person visit "today" page the "lat visit"
    # probably should not be reset completely
    if len(papers['papers']) > 0 and papers['papers'][0].get('date_up'):
        # update the date of last visit
        current_user.login = datetime.now()
        current_user.last_paper = papers['papers'][0]['date_up']
        db.session.commit()

    papers = process_papers(papers,
                            session['tags'],
                            session['cats'],
                            do_nov=True,
                            do_tag=True
                            )
    render_papers(papers, sort=True)

    result = {'papers': papers['papers'],
              'ncat': papers['n_cats'],
              'ntag': papers['n_tags'],
              'nnov': papers['n_nov']
              }
    return jsonify(result)

@main_bp.route('/about')
def about():
    """About page."""
    load_prefs()
    dark = session.get('pref') and session['pref'].get('dark')
    return render_template('about.jinja2',
                           dark=dark
                           )

##### Bookshelf stuff ##################################################
@main_bp.route('/bookshelf')
@login_required
def bookshelf():
    """Bookshelf page."""
    # if list is not specified take the default one
    if 'list' not in request.args:
        return redirect(url('main_bp.bookshelf', list=DEFAULT_LIST))
    display_list = request.args['list']

    lists = []
    # get all lists for the menu
    paper_lists = PaperList.query.filter_by(user_id=current_user.id).all()
    if len(paper_lists) == 0:
        new_default_list(current_user.id)
        paper_lists = PaperList.query.filter_by(user_id=current_user.id).all()

    for paper_list in paper_lists:
        lists.append(paper_list.name)

    # get papers in the list
    paper_list = PaperList.query.filter_by(user_id=current_user.id,
                                           name=display_list
                                           ).first()

    papers = {'list': lists[0],
              'papers': []
              }

    # TODO sort by update date, not by added to bookmarks date
    for paper in paper_list.papers:
        papers['papers'].append(render_paper_json(paper))

    papers = process_papers(papers,
                            session['tags'],
                            session['cats'],
                            do_nov=False,
                            do_tag=True
                            )

    render_papers(papers, sort=False)

    return render_template('bookshelf.jinja2',
                           papers=papers,
                           lists=lists,
                           displayList=display_list,
                           tags=session['tags'],
                           math_jax=session['pref'].get('tex'),
                           dark=session['pref'].get('dark')
                           )

@main_bp.route('/add_bm', methods=['POST'])
@login_required
def add_bm():
    """
    Add bookmark.

    Take paper_id as an input and add a reference to the paper
    to the given paper list
    """
    # read input
    paper_id = request.form.get('paper_id')

    # search if paper is already in the paper DB
    paper = Paper.query.filter_by(paper_id=paper_id).first()
    # if paper is not in the paper table
    # cerate a new one
    if not paper:
        return dumps({'success':False}), 422

    # in case no list is there
    # create a new one
    # WARNING work with one list for the time beeing
    paper_list = PaperList.query.filter_by(user_id=current_user.id).first()
    if not paper_list:
        # create a default list
        new_default_list(current_user.id)
        paper_list = PaperList.query.filter_by(user_id=current_user.id).first()

    # check if paper is already in the given list of the current user
    result = db.session.query(paper_associate).filter_by(list_ref_id=paper_list.id,
                                                         paper_ref_id=paper.id
                                                         ).first()
    if result:
        return dumps({'success':True}), 200

    paper_list.papers.append(paper)
    db.session.commit()
    return dumps({'success':True}), 201


@main_bp.route('/del_bm', methods=['POST'])
@login_required
def del_bm():
    """Delete bookmark."""
    paper_id = request.form.get('paper_id')
    paper = Paper.query.filter_by(paper_id=paper_id).first()
    if not paper:
        return dumps({'success':False}), 204
    # WARNING work with one list for the time beeing
    paper_list = PaperList.query.filter_by(user_id=current_user.id).first()

    paper_list.papers.remove(paper)
    db.session.commit()
    return dumps({'success':True}), 201

######### Daemon functions #############################################

@main_bp.route('/load_papers', methods=['GET'])
def load_papers():
    """Load papers and store in the database."""
    # auth stuff
    logging.info('Start paper table update')
    if current_app.config['TOKEN'] != request.args.get('token'):
        logging.error('Wrong token')
        return dumps({'success':False}), 422

    # last paper in the DB
    last_paper = Paper.query.order_by(Paper.date_up.desc()).first()
    today_date = datetime.now()
    if not last_paper:
        # if no last paper download for this month
        last_paper_date = today_date - timedelta(days=today_date.day)
    else:
        last_paper_date = last_paper.date_up - timedelta(days=1)

    # update_papers() params
    # by default updates are on
    params = {'do_update': True}
    if 'n_papers' in request.args:
        params['n_papers'] = int(request.args.get('n_papers'))
    if 'do_update' in request.args:
        params['do_update'] = request.args.get('do_update')
    if 'from' in request.args:
        params['last_paper_date'] = datetime.strptime(request.args['from'],
                                            '%Y-%m-%d'
                                             )
    else:
        params['last_paper_date'] = last_paper_date

    logging.info('Parameters: %s', params)

    # initiaise paper API
    paper_api = ArxivOaiApi()

    # API cal params
    if request.args.get('set'):
        paper_api.set_set(request.args.get('set'))
    # from argument is privelaged over last paper in the DB
    if request.args.get('from'):
        paper_api.set_from(request.args.get('set'))
    else:
        paper_api.set_from(datetime.strftime(last_paper_date,
                                             '%Y-%m-%d'
                                             ))

    # further code is paper source independent.
    # Any API can be defined above
    update_papers([paper_api], **params)

    return dumps({'success':True}), 201

@main_bp.route('/bookmark_papers', methods=['GET'])
def bookmark_papers():
    """Auto bookmark new submissions."""

@main_bp.route('/email_papers', methods=['GET'])
def email_papers():
    """Email notifications about new submissions."""

@main_bp.route('/public_tags', methods=['GET'])
def public_tags():
    """Get puclicly available tags as examples."""
