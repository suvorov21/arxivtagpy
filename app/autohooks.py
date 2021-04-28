"""
Module with daemon functions that work are triggered by hooks.

1. Paper downloading
2. Auto bookmarks
3. Emails
"""

from datetime import datetime, timedelta
import logging
from json import dumps
from typing import Dict, List
from functools import wraps

from flask import Blueprint, current_app, request
from flask_mail import Message

from .model import User, Tag, db, PaperList, Paper, UpdateDate, \
paper_associate
from .papers import tag_suitable, render_paper_json, update_papers
from .paper_api import ArxivOaiApi
from . import mail


auto_bp = Blueprint(
    'auto_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)

def check_token(funct):
    """
    Decorator that checks the token.

    Used in the autometic functions for verifications.
    """
    @wraps(funct)
    def my_wrapper(*args, **kwargs):
        if current_app.config['TOKEN'] != request.args.get('token'):
            logging.error('Wrong token')
            return dumps({'success':False}), 422
        return funct(*args, **kwargs)

    return my_wrapper

@auto_bp.route('/load_papers', methods=['GET'])
@check_token
def load_papers():
    """Load papers and store in the database."""
    # auth stuff
    logging.info('Start paper table update')

    # last paper in the DB
    last_paper = Paper.query.order_by(Paper.date_up.desc()).first()

    if not last_paper:
        # if no last paper download for this month
        last_paper_date = month_start()
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
        last_paper_date = datetime.strptime(request.args['from'],
                                            '%Y-%m-%d'
                                            )
    params['last_paper_date'] = last_paper_date

    logging.info('Parameters: %s', params)

    # initiaise paper API
    paper_api = ArxivOaiApi()

    # API cal params
    if request.args.get('set'):
        paper_api.set_set(request.args.get('set'))
    # from argument is privelaged over last paper in the DB
    paper_api.set_from(datetime.strftime(last_paper_date,
                                         '%Y-%m-%d'
                                         ))

    # further code is paper source independent.
    # Any API can be defined above
    update_papers([paper_api], **params)

    return dumps({'success':True}), 201

@auto_bp.route('/bookmark_papers', methods=['GET'])
@check_token
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

    tags = Tag.query.filter_by(bookmark=True).order_by(Tag.user_id)

    # the date until one the papers will be processed
    old_date_record = get_old_update_date()
    old_date = old_date_record.last_bookmark

    if 'from' in request.args:
        old_date = datetime.strptime(request.args['from'],
                                     '%Y-%m-%d'
                                     )

    prev_user = -1

    n_user = 0
    n_papers = 0
    for tag in tags:
        # 2
        if tag.user_id != prev_user:
            logging.debug('Bookmark for user %i', tag.user_id)
            user = User.query.filter_by(id=tag.user_id).first()
            # 2.3 query papers with user's cats
            papers = Paper.query.filter(Paper.cats.overlap(user.arxiv_cat),
                                        Paper.date_up > old_date
                                        ).order_by(Paper.date_up).all()
            prev_user = tag.user_id
            n_user += 1
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
                # check if paper is already there to prevent dublicatiopn
                result = db.session.query(paper_associate
                                          ).filter_by(list_ref_id=paper_list.id,
                                                      paper_ref_id=paper.id
                                                      ).first()
                if not result:
                    paper_list.papers.append(paper)
                    n_papers += 1

    # store the last checked paper
    last_paper = Paper.query.order_by(Paper.date_up.desc()).first()
    old_date_record.last_bookmark = last_paper.date_up
    db.session.commit()
    logging.info('Done with bookmarks. Users %r, papers, %s',
                 n_user,
                 n_papers
                 )

    return dumps({'success':True}), 201


@auto_bp.route('/email_papers', methods=['GET'])
@check_token
def email_papers():
    """
    Email notifications about new submissions.

    1. Start with quering all the tags with email==True
        sort by user id
    2. User by user:
        2.1 Get a user that owns this tag
        2.2 Get cats this user is interested in
        2.3 Query papers since last run with the categories of a given user
    3. papers_to_send = []. tag by tag:
        3.1 Paper by paper:
            3.2.1 Check if tag_suitable -- add paper to the papers_to_send
    4. Render email with papers_to_send and send.
    """
    do_send = request.args.get('do_send')
    logging.info('Start paper email sending update do_send=%r', do_send)

    tags = Tag.query.filter_by(email=True).order_by(Tag.user_id)

    # the date until one the papers will be processed
    old_date_record = get_old_update_date()
    old_date = old_date_record.last_email

    prev_user = -1
    papers_to_send = []
    n_user = 0
    n_papers = 0
    for tag in tags:
        # 2
        if tag.user_id != prev_user:
            logging.debug('Bookmark for user %i', tag.user_id)
            user = User.query.filter_by(id=tag.user_id).first()
            # 2.3 query papers with user's cats
            papers = Paper.query.filter(Paper.cats.overlap(user.arxiv_cat),
                                        Paper.date_up > old_date
                                        ).order_by(Paper.date_up).all()
            # 4. send papers
            if any([len(tags['papers']) > 0 for tags in papers_to_send]):
                email_paper_update(papers_to_send, user.email, do_send)

            prev_user = tag.user_id
            n_user += 1
            papers_to_send = [{'tag': tag.name,
                               'papers': []
                               }]

        # 3.2
        for paper in papers:
            if tag_suitable(render_paper_json(paper), tag.rule):
                papers_to_send[-1]['papers'].append(paper)
                n_papers += 1


    # for the last user
    if any([len(tags['papers']) > 0 for tags in papers_to_send]):
        email_paper_update(papers_to_send, user.email, bool(do_send))


    # store the last checked paper
    last_paper = Paper.query.order_by(Paper.date_up.desc()).first()
    old_date_record.last_email = last_paper.date_up
    db.session.commit()

    logging.info('Done with emails. Users %r, papers, %s',
                 n_user,
                 n_papers
                 )
    return dumps({'success':True}), 201

def month_start():
    """Return the first day of the month."""
    today_date = datetime.now()
    return today_date - timedelta(days=today_date.day)

def email_paper_update(papers: List[Dict], email: str, do_send: bool):
    """Send the papers update."""
    body = 'Hello,\n\nWe created a daily paper feed based on your preferences.'
    for paper_tag in papers:
        body += '\n\nFor tag ' + paper_tag['tag'] + ':\n'
        for number, paper in enumerate(paper_tag['papers']):
            body += f'{str(number+1)}. {paper.title}\n'

    body += '\n\n\nRegards, \narXiv tag team.'
    msg = Message(body=body,
                  sender="noreply@arxivtag.tk",
                  recipients=[email],
                  subject="arXiv tag paper feed"
                  )

    if do_send:
        mail.send(msg)

def get_old_update_date() -> UpdateDate:
    """Chech if the database record with latest update exists. If not create."""
    old_date_record = UpdateDate.query.first()
    if not old_date_record:
        old_date = month_start()
        old_date_record = UpdateDate(last_bookmark=old_date,
                                     last_email=old_date)
        db.session.add(old_date_record)
        db.session.commit()

    return old_date_record
