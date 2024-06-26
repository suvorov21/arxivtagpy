"""
Module with daemon functions that work are triggered by hooks.

1. Paper downloading
2. Auto bookmarks
3. Emails
"""

import logging
from datetime import datetime, timedelta
from functools import wraps
from json import dumps
from typing import List

from feedgen.feed import FeedGenerator
from flask import Blueprint, current_app, request, render_template, make_response, redirect, url_for, flash
from flask_login import current_user
from flask_mail import Message

from .interfaces.data_structures import PaperInterface, PaperResponse, TagInterface
from .interfaces.model import User, Tag, db, Paper, \
    paper_associate, PaperCacheDay, PaperCacheWeeks
from .paper_api import ArxivOaiApi
from .paper_db import update_papers
from .papers import tag_suitable, process_papers
from .routes import get_papers
from .utils import decode_token, DecodeException
from .utils_app import mail_catch, get_or_create_list, get_old_update_date

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
        if current_app.config['TOKEN'] != request.headers.get('token'):
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
    old_date_record = get_old_update_date()
    last_paper_date = old_date_record.last_paper - timedelta(days=1)

    # update_papers() params
    # by default updates are on
    params = {'do_update': True}
    if 'n_papers' in request.args:
        params['n_papers'] = int(request.args.get('n_papers'))
    if 'do_update' in request.args:
        params['do_update'] = request.args.get('do_update')
    if 'start_date' in request.args:
        last_paper_date = datetime.strptime(request.args['start_date'],
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
    else:
        paper_api.params.pop('until', None)

    # further code is paper source independent.
    # Any API can be defined above
    update_papers([paper_api], **params)

    # update the date record
    last_paper = Paper.query.order_by(Paper.date_up.desc()).limit(1).first()
    old_date_record.last_paper = last_paper.date_up
    db.session.commit()

    # update the cache
    # Day cache
    PaperCacheDay.query.delete()
    keys = db.inspect(PaperCacheDay).columns.keys()
    get_columns = lambda post: {key: getattr(post, key) for key in keys}

    posts = Paper.query.filter(Paper.date_up > old_date_record.last_paper - timedelta(days=1))
    db.session.bulk_insert_mappings(PaperCacheDay, (get_columns(post) for post in posts))
    old_date_record.first_paper_day_cache = PaperCacheDay.query.order_by(
        PaperCacheDay.date_up.asc()
    ).limit(1).first().date_up

    # Week cache
    PaperCacheWeeks.query.delete()
    keys = db.inspect(PaperCacheWeeks).columns.keys()
    get_columns = lambda post: {key: getattr(post, key) for key in keys}

    posts = Paper.query.filter(Paper.date_up > old_date_record.last_paper - timedelta(days=14))
    db.session.bulk_insert_mappings(PaperCacheWeeks, (get_columns(post) for post in posts))
    old_date_record.first_paper_weeks_cache = PaperCacheWeeks.query.order_by(
        PaperCacheWeeks.date_up.asc()
    ).limit(1).first().date_up

    db.session.commit()

    # TODO move it to particular API
    if abs(old_date_record.last_paper.hour - current_app.config['ARXIV_DEADLINE_TIME'].hour) > 1:
        logging.warning('Last paper exceeds deadline limit! Consider deadline revision')
        logging.warning('Last paper: %r\tDeadline: %r',
                        last_paper_date,
                        current_app.config['ARXIV_DEADLINE_TIME']
                        )

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

    if request.args.get('force'):
        to_delete = Paper.query.filter(Paper.date_up < until_date)
    else:
        # WARNING may be not so elegant and fast
        bookmarked = db.session.query(paper_associate.columns.paper_ref_id).distinct(
            paper_associate.columns.paper_ref_id)
        to_delete = db.session.query(Paper).filter(Paper.id.not_in(bookmarked))

    #  Paper.date_up < until_date)
    logging.info('Deleting %i papers', len(to_delete.all()))
    n_deleted = len(to_delete.all())
    to_delete.delete(synchronize_session=False)
    db.session.commit()

    logging.info('All papers until %r are deleted.', until_date)

    return dumps({'success': True, 'deleted': n_deleted}), 201


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
        if tag_suitable(PaperInterface.from_paper(paper), rule):
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

    if 'start_date' in request.args:
        old_date = datetime.strptime(request.args['start_date'],
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
            if tag_suitable(PaperInterface.from_paper(paper), tag.rule):
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
                email_paper_update(papers_to_send,
                                   user.email,
                                   bool(do_send.lower() == "true") and user.verified_email
                                   )

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
            if tag_suitable(PaperInterface.from_paper(paper), tag.rule):
                papers_to_send[-1]['papers'].append(paper)
                n_papers += 1

    # for the last user
    if any([len(tags['papers']) > 0 for tags in papers_to_send]):
        logging.debug('Send email for user %i', user.id)
        email_paper_update(papers_to_send,
                           user.email,
                           bool(do_send == "True") and user.verified_email
                           )

    # store the last checked paper
    last_paper = Paper.query.order_by(Paper.date_up.desc()).first()
    old_date_record.last_email = last_paper.date_up
    db.session.commit()

    logging.info('Done with emails. Users %r, papers %s',
                 n_user,
                 n_papers
                 )
    return dumps({'success': True}), 201


def email_paper_update(papers: List, email: str, do_send: bool):
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
            ref_pdf = ArxivOaiApi.get_ref_pdf(paper.paper_id,
                                              paper.version
                                              )

            ref_arxiv = ArxivOaiApi.get_ref_web(paper.paper_id,
                                                paper.version
                                                )
            # paper version
            if paper.version != 'v1':
                html_body += f'<span class="small gray">{paper.version}'
                html_body += f' (v1: {datetime.strftime(paper.date_sub, "%d %B %Y")})<br>'
                html_body += '</span>'

            # Categories
            html_body += f'<span class="small">[<b>{paper.cats[0]}</b>'
            for cat in paper.cats[1:]:
                html_body += f', {cat}'
            html_body += ']</span><br>'

            # link to website
            html_body += f'<a href={ref_arxiv}>arXiv</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href={ref_pdf}>PDF</a></p>'

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


@auto_bp.route('/rss/<token>')
def rss_feed(token):
    """Hook for an RSS feed."""
    try:
        data = decode_token(token, keys=['user'])
    except DecodeException:
        flash('Wrong RSS token received')
        logging.error('Wrong RSS token received')
        return redirect(url_for('settings_bp.settings_page', page='pref'), code=303)

    print('Checking user ', data['user'])
    user = User.query.filter_by(email=data['user']).first()

    # create feed generator
    fg = FeedGenerator()
    fg.title('arXiv tag RSS feed')
    fg.description('Feed with your tags')
    fg.link(href=f'https://arxivtag.com/rss/{token}')

    # fill the paper list
    new_date = datetime.now()
    old_date = new_date - timedelta(days=14)

    response = PaperResponse(old_date)
    response.papers = get_papers(user.arxiv_cat, old_date, new_date)

    tag_list = []
    # use only RSS tags for speedup
    tags = Tag.query.filter_by(user_id=user.id, userss=True).order_by(Tag.order).all()
    for tag in tags:
        tag_list.append(TagInterface.from_tag(tag))
    # assign tags
    process_papers(response,
                   tag_list,
                   [''],
                   do_nov=False,
                   do_tag=True
                   )

    response.sort_papers()
    # Add entries to feed
    for paper in response.papers:
        # only if one of the RSS tags is assigned
        if len(paper.tags) > 0:
            fe = fg.add_entry()
            prefix = 'https'
            fe.id(f'{prefix}://{request.headers["Host"]}/rss/id/{paper.id}')
            fe.title(paper.title)
            fe.author(name=paper.author)
            fe.description(paper.abstract)
            fe.published(paper.date_sub.strftime('%d %B %Y') + ' 00:00Z')
            fe.link({'href': ArxivOaiApi.get_ref_web(paper.paper_id, paper.version),
                     'rel': 'alternate',
                     'type': 'webpage',
                     'hreflang': 'en-US',
                     'title': 'Link to arXiv'
                     })

    # return a feed
    response = make_response(fg.rss_str())
    response.headers.set('Content-Type', 'application/rss+xml')

    return response
