"""
Module with daemon functions that work are triggered by hooks.

1. Paper downloading
2. Auto bookmarks
3. Emails
"""

from datetime import datetime, timedelta
import logging
from json import dumps
from functools import wraps

from flask import Blueprint, current_app, request, render_template
from flask_mail import Message
from flask_login import current_user

from .model import User, Tag, db, Paper, UpdateDate, \
    paper_associate
from .papers import tag_suitable, render_paper_json, update_papers
from .paper_api import ArxivOaiApi
from .utils import mail_catch, get_or_create_list

auto_bp = Blueprint(
    'auto_bp',
    __name__,
    template_folder='templates',
    static_folder='frontend'
)

DATA_FORMAT = '%Y-%m-%d'


def check_token(funct):
    """
    Decorator that checks the token.

    Used in the automatic functions for verifications.
    """

    @wraps(funct)
    def my_wrapper(*args, **kwargs):
        if current_app.config['TOKEN'] != request.args.get('token'):
            logging.error('Wrong token')
            return dumps({'success': False}), 422
        return funct(*args, **kwargs)

    return my_wrapper


@auto_bp.route('/load_papers', methods=['POST'])
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
                                            DATA_FORMAT
                                            )
    params['last_paper_date'] = last_paper_date

    logging.info('Parameters: %s', params)

    # initialise paper API
    paper_api = ArxivOaiApi()

    # API cal params
    if request.args.get('set'):
        paper_api.set_set(request.args.get('set'))
    # from argument is privileged over last paper in the DB
    paper_api.set_from(datetime.strftime(last_paper_date,
                                         DATA_FORMAT
                                         ))

    if request.args.get('until'):
        paper_api.set_until(request.args['until'])

    # further code is paper source independent.
    # Any API can be defined above
    update_papers([paper_api], **params)

    return dumps({'success': True}), 201


@auto_bp.route('/delete_papers', methods=['POST'])
@check_token
def delete_papers():
    """Clean up paper table."""
    logging.info('Start paper delete')
    if 'until' in request.args:
        until_date = datetime.strptime(request.args['until'],
                                       DATA_FORMAT
                                       )
    elif 'week' in request.args:
        n_weeks = int(request.args['week'])
        until_date = datetime.now() - timedelta(days=7 * n_weeks)
    elif 'days' in request.args:
        n_days = int(request.args['days'])
        until_date = datetime.now() - timedelta(n_days)
    else:
        logging.error('Options are not provided. Exit to prevent DB damage.')
        return dumps({'success': False}), 422

    Paper.query.filter(Paper.date_up < until_date).delete()
    db.session.commit()

    logging.info('All papers until %r are deleted.', until_date)

    return dumps({'success': True}), 201


@auto_bp.route('/bookmark_papers_user', methods=['POST'])
def bookmark_user():
    """Bookmarks papers for a given user for the last months."""
    name = request.form.to_dict().get('name')

    # by default work with current user
    # but in principle any user could be triggered, but token is required
    email = request.form.to_dict().get('email')
    if email and \
            request.form.to_dict().get('token') == current_app.config['TOKEN']:
        usr = User.query.filter_by(email=email).first()
    elif current_user.is_authenticated:
        usr = current_user
    else:
        logging.error('Bad bookmark request %r', request.form)
        return dumps({'success': False}), 422

    try:
        weeks = int(request.form.to_dict().get('weeks'))
    except (TypeError, ValueError):
        weeks = 4

    if not name:
        logging.error('Tag name is not specified')
        return dumps({'success': False}), 422

    tag = Tag.query.filter_by(name=name,
                              user_id=usr.id
                              ).first()

    rule = request.form.to_dict().get('rule')

    if not rule and not tag:
        logging.error('Bad bookmark request %r', request.form)
        return dumps({'success': False}), 422

    if not rule:
        rule = tag.rule

    old_date = datetime.now() - timedelta(weeks=weeks)
    papers = Paper.query.filter(Paper.cats.overlap(usr.arxiv_cat),
                                Paper.date_up > old_date
                                ).order_by(Paper.date_up).all()

    paper_list = get_or_create_list(usr.id, name)

    for paper in papers:
        if tag_suitable(render_paper_json(paper), rule):
            # check if paper is already there to prevent duplication
            result = db.session.query(paper_associate
                                      ).filter_by(list_ref_id=paper_list.id,
                                                  paper_ref_id=paper.id
                                                  ).first()
            if not result:
                paper_list.papers.append(paper)
                paper_list.not_seen += 1

    db.session.commit()
    return dumps({'success': True}), 201


@auto_bp.route('/bookmark_papers', methods=['POST'])
@check_token
def bookmark_papers():
    """
    Auto bookmark new submissions.

    1. Start with querying all the tags with bookmark==True
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

    tags = Tag.query.filter_by(bookmark=True).order_by(Tag.user_id).all()

    # the date until one the papers will be processed
    old_date_record = get_old_update_date()
    old_date = old_date_record.last_bookmark

    if 'from' in request.args:
        old_date = datetime.strptime(request.args['from'],
                                     DATA_FORMAT
                                     )

    prev_user = -1

    n_user = 0
    n_papers = 0
    papers = []
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
        paper_list = get_or_create_list(prev_user, tag.name)

        # 3.2
        for paper in papers:
            if tag_suitable(render_paper_json(paper), tag.rule):
                # check if paper is already there to prevent duplication
                result = db.session.query(paper_associate
                                          ).filter_by(list_ref_id=paper_list.id,
                                                      paper_ref_id=paper.id
                                                      ).first()
                if not result:
                    paper_list.papers.append(paper)
                    n_papers += 1
                    paper_list.not_seen += 1

    # store the last checked paper
    last_paper = Paper.query.order_by(Paper.date_up.desc()).first()
    old_date_record.last_bookmark = last_paper.date_up
    db.session.commit()
    logging.info('Done with bookmarks. Users %r, papers %s',
                 n_user,
                 n_papers
                 )

    return dumps({'success': True}), 201


@auto_bp.route('/email_papers', methods=['POST'])
@check_token
def email_papers():
    """
    Email notifications about new submissions.

    1. Start with querying all the tags with email==True
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

    tags = Tag.query.filter_by(email=True).order_by(Tag.user_id,
                                                    Tag.order
                                                    ).all()

    # the date until one the papers will be processed
    old_date_record = get_old_update_date()
    old_date = old_date_record.last_email

    prev_user = -1
    papers_to_send = []
    n_user = 0
    n_papers = 0
    user = None
    papers = []
    for tag in tags:
        # 2
        if tag.user_id != prev_user:
            # 4. send papers. If tags['papers'] is empty
            #  --> the first user is processing
            if any([len(tags['papers']) > 0 for tags in papers_to_send]) \
                    and user:
                logging.debug('Send email for user %i', user.id)
                email_paper_update(papers_to_send, user.email, bool(do_send == "True"))

            user = User.query.filter_by(id=tag.user_id).first()
            logging.debug('Form the email for user %i', user.id)
            # 2.3 query papers with user's cats
            papers = Paper.query.filter(Paper.cats.overlap(user.arxiv_cat),
                                        Paper.date_up > old_date
                                        ).order_by(Paper.date_up).all()

            prev_user = tag.user_id
            n_user += 1
            papers_to_send = []

        papers_to_send.append({'tag': tag.name,
                               'papers': []
                               })
        # 3.2
        for paper in papers:
            if tag_suitable(render_paper_json(paper), tag.rule):
                papers_to_send[-1]['papers'].append(paper)
                n_papers += 1

    # for the last user
    if any([len(tags['papers']) > 0 for tags in papers_to_send]):
        logging.debug('Send email for user %i', user.id)
        email_paper_update(papers_to_send, user.email, bool(do_send == "True"))

    # store the last checked paper
    last_paper = Paper.query.order_by(Paper.date_up.desc()).first()
    old_date_record.last_email = last_paper.date_up
    db.session.commit()

    logging.info('Done with emails. Users %r, papers %s',
                 n_user,
                 n_papers
                 )
    return dumps({'success': True}), 201


def month_start() -> datetime:
    """Return the first day of the month."""
    today_date = datetime.now()
    # if month just stated --> take the previous one
    if today_date.day < 3:
        today_date -= timedelta(days=4)
    return today_date - timedelta(days=today_date.day)


def email_paper_update(papers: list, email: str, do_send: bool):
    """Send the papers update."""
    body = 'Hello,\n\nWe created a daily paper feed based on your preferences.'
    html_body = ''
    for paper_tag in papers:
        if len(paper_tag['papers']) == 0:
            continue
        body += '\n\nFor tag ' + paper_tag['tag'] + ':\n'
        html_body += f'<br/><h3>Fot tag {paper_tag["tag"]}:</h3>'
        for number, paper in enumerate(paper_tag['papers']):
            body += f'{str(number + 1)}. {paper.title}\n'
            html_body += f'<p>{str(number + 1)}. {paper.title}<br/>'
            ref_pdf = ArxivOaiApi().get_ref_pdf(paper.paper_id,
                                                paper.version
                                                )

            ref_arxiv = ArxivOaiApi().get_ref_web(paper.paper_id,
                                                  paper.version
                                                  )
            html_body += f'<a href={ref_arxiv}>arXiv</a> | <a href={ref_pdf}>PDF</a></p>'

    body += '\n\n\n\nRegards, \narXiv tag team.'

    html = render_template('mail_feed.jinja2',
                           papers=html_body,
                           host=request.headers['Host']
                           )

    msg = Message(body=body,
                  html=html,
                  sender=current_app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[email],
                  subject="arXiv tag paper feed"
                  )

    if do_send:
        mail_catch(msg)


def get_old_update_date() -> UpdateDate:
    """Check if the database record with latest update exists. If not create."""
    old_date_record = UpdateDate.query.first()
    if not old_date_record:
        old_date = month_start()
        old_date_record = UpdateDate(last_bookmark=old_date,
                                     last_email=old_date)
        db.session.add(old_date_record)
        db.session.commit()

    return old_date_record
