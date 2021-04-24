"""
Module with daemon functions that work are triggered by hooks.

1. Paper downloading
2. Auto bookmarks
3. Emails
"""

from datetime import datetime, timedelta
import logging
from json import dumps

from flask import Blueprint, current_app, request

from .model import User, Tag, db, PaperList, Paper
from .papers import tag_suitable, render_paper_json, update_papers
from .paper_api import ArxivOaiApi


auto_bp = Blueprint(
    'auto_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)

@auto_bp.route('/load_papers', methods=['GET'])
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

@auto_bp.route('/bookmark_papers', methods=['GET'])
def bookmark_papers():
    """
    Auto bookmark new submissions.

    1. Start with quering all the tags with bookmark==True
        sort by user id
    2. User by user:
        2.1 Get a user that owns this tag
        2.2 Get cats this user is interested in
        2.3 Query papers since last run with the categories of a given user
    3. tag by tag:
        3.1 Check that for a given user paper list exists. If not -- create
        3.2 Paper by paper:
            3.2.1 Check if tag_suitable -- add paper to the list
    """
    logging.info('Start paper bookmark update')
    if current_app.config['TOKEN'] != request.args.get('token'):
        logging.error('Wrong token')
        return dumps({'success':False}), 422

    tags = Tag.query.filter_by(bookmark=True).order_by(Tag.user_id)

    prev_user = -1

    old_date = datetime(2020, 3, 3)

    for tag in tags:
        # 2
        if tag.user_id != prev_user:
            user = User.query.filter_by(id=tag.user_id).first()
            # 2.3 query papers with user's cats
            papers = Paper.query.filter(Paper.cats.overlap(user.arxiv_cat),
                                        Paper.date_up > old_date
                                        ).all()
            prev_user = tag.user_id
        # 3.1
        paper_list = PaperList.query.filter_by(user_id=prev_user,
                                               name=tag.name
                                               ).first()
        # if not --> create one
        if not paper_list:
            paper_list = PaperList(name=tag.name,
                                   user_id=prev_user
                                   )
            db.session.add(paper_list)
            db.session.commit()

        # 3.2
        for paper in papers:
            if tag_suitable(render_paper_json(paper), tag.rule):
                paper_list.papers.append(paper)

    db.session.commit()

    logging.info('Done with bookmarks.')

    return dumps({'success':True}), 201


@auto_bp.route('/email_papers', methods=['GET'])
def email_papers():
    """Email notifications about new submissions."""
    logging.info('Start paper email sending update')
    if current_app.config['TOKEN'] != request.args.get('token'):
        logging.error('Wrong token')
        return dumps({'success':False}), 422

    return dumps({'success':True}), 201