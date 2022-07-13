"""Main blueprint with all the main pages."""

from datetime import datetime, timezone, timedelta
from json import dumps, loads
import logging

from flask import Blueprint, render_template, session, redirect, request, jsonify, url_for
from flask_login import current_user, login_required
from flask_mail import Message

from . import mail
from .interfaces.model import db, Paper, PaperList, paper_associate, Tag
from .interfaces.data_structures import PaperResponse, PaperInterface, TagInterface
from .auth import new_default_list

from .papers import process_papers, get_papers, get_unseen_papers, tag_suitable
from .paper_api import get_arxiv_sub_start, get_announce_date, get_arxiv_announce_date, get_date_range
from .utils_app import get_lists_for_user, get_old_update_date, update_seen_papers
from .settings import default_data
from .utils import render_title

PAPERS_PAGE = 25
RECENT_PAPER_RANGE = 10

main_bp = Blueprint(
    'main_bp',
    __name__,
    template_folder='templates',
    static_folder='frontend'
)

ROOT_LISTS = 'main_bp.papers_list'
ROOT_BOOK = 'main_bp.bookshelf'


@main_bp.route('/')
def root():
    """Landing page."""
    if current_user.is_authenticated:
        session['pref'] = loads(current_user.pref)
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.paper_land'))

    return render_template('about.jinja2',
                           data=default_data()
                           )


@main_bp.route('/papers')
@login_required
def papers_list():
    """Papers list page."""
    date_type = request.args.get('date')
    # date is obligatory argument
    if date_type is None:
        return redirect(url_for(ROOT_LISTS,
                                date='today',
                                **request.args
                                ))

    # page is obligatory for front-end rendering
    if request.args.get('page') is None:
        return redirect(url_for(ROOT_LISTS,
                                **request.args,
                                page='1'
                                ))

    # load preferences
    # TODO load only certain columns?
    tags_db = Tag.query.filter_by(user_id=current_user.id).order_by(Tag.order).all()
    tags_inter = [TagInterface.from_tag(tag) for tag in tags_db]

    # get rid of tag rule at front-end
    tags_list = [tag.to_front() for tag in tags_inter]

    return render_template('papers.jinja2',
                           title=render_title(date_type),
                           cats=current_user.arxiv_cat,
                           tags=dumps(tags_list),
                           data=default_data()
                           )


@main_bp.route('/paper_land')
@login_required
def paper_land():
    """Access to the paper range selector page."""
    session['pref'] = loads(current_user.pref)

    announce_date = get_announce_date()

    update_recent_papers(announce_date)

    # loop over past week and see what days have been seen
    past_week = []
    today = get_announce_date()
    count = 0
    for i in range(RECENT_PAPER_RANGE):
        # display only last week
        if count > 6:
            break
        day = today - timedelta(days=i)
        # skip weekend
        if day.weekday() > 4:
            past_week.append({'day': ''})
            continue

        visit = bool(current_user.recent_visit & (2 ** i))
        href = '{url}?date=range&from={fr}&until={until}'
        from_str = datetime.strftime(day, '%d-%m-%Y')
        until_str = datetime.strftime(day, '%d-%m-%Y')
        past_week.append({'day': datetime.strftime(day, '%A, %d %B'),
                          'href': href.format(url=url_for(ROOT_LISTS),
                                              fr=from_str,
                                              until=until_str
                                              ),
                          'visit': visit
                          })
        count += 1

    last_visit_date = get_arxiv_announce_date(current_user.last_paper)
    return render_template('paper_land.jinja2',
                           data=default_data(),
                           last_visit=datetime.strftime(last_visit_date,
                                                        '%d %b %Y'
                                                        ),

                           past_week=past_week
                           )


@main_bp.route('/data')
@login_required
def data():
    """API for paper download and process."""
    announce_date = get_announce_date()

    # update the information about "seen" papers since the last visit
    update_recent_papers(announce_date)

    old_date_tmp, new_date_tmp, new_date = get_date_range(
        request.args['date'],
        announce_date,
        fr=request.args.get('from'),
        un=request.args.get('until')
    )

    old_date = get_arxiv_sub_start(old_date_tmp.date())
    # papers since last visit is a special case,
    # the last paper date is read from DB
    if request.args['date'] == 'last':
        old_date = current_user.last_paper
        old_date_tmp = get_arxiv_announce_date(current_user.last_paper)

    logging.debug('Now: %r\nNew date: %r\nOld_date: %r',
                  datetime.now(timezone.utc),
                  new_date,
                  old_date
                  )

    response = PaperResponse(old_date)

    # update "seen" papers bounds
    it_start = (announce_date -
                new_date_tmp.replace(tzinfo=timezone.utc)).days
    it_end = (announce_date -
              old_date_tmp.replace(tzinfo=timezone.utc)).days

    # define categories of interest
    cats = current_user.arxiv_cat

    if request.args['date'] != 'unseen':
        response.papers = get_papers(cats,
                                     old_date,
                                     new_date
                                     )
    else:
        it_start = 0
        it_end = RECENT_PAPER_RANGE
        response.papers = get_unseen_papers(cats,
                                            current_user.recent_visit,
                                            RECENT_PAPER_RANGE,
                                            announce_date)

    update_seen_papers(it_start, min(RECENT_PAPER_RANGE, it_end))

    # because of the holidays 1-2 day can be skipped
    # in this case return the last day with submissions
    if len(response.papers) == 0 and request.args['date'] in ('today', 'week', 'month'):
        last_paper_date = get_old_update_date().last_paper
        # update information for the page title
        old_date_tmp, new_date_tmp, new_date = get_date_range(
            request.args['date'],
            get_arxiv_announce_date(last_paper_date)
        )
        # new query in the paper DB. Attempt to find papers
        response.papers = get_papers(cats,
                                     last_paper_date - timedelta(days=int(request.args['date'] == 'today'),
                                                                 weeks=int(request.args['date'] == 'week') +
                                                                 4 * int(request.args['date'] == 'month')),
                                     last_paper_date
                                     )

    # error handler
    # "last" and "unseen" papers query results are allowed to be empty
    if len(response.papers) == 0 and \
            request.args['date'] not in ('last', 'unseen'):
        logging.warning('No papers suitable with request')
        return jsonify(response)

    # store the info about last checked paper
    # descending paper order is assumed
    if len(response.papers) > 0 and response.papers[0].date_up:
        # update the date of last visit
        current_user.login = announce_date.replace(tzinfo=None)
        # update last seen paper only if browsing papers until the last one
        current_user.last_paper = max(response.papers[0].date_up, current_user.last_paper)
        logging.debug('RV %r', format(current_user.recent_visit, 'b'))
        db.session.commit()

    tags_db = Tag.query.filter_by(user_id=current_user.id).order_by(Tag.order).all()
    tags_inter = [TagInterface.from_tag(tag) for tag in tags_db]

    process_papers(response,
                   tags_inter,
                   cats,
                   do_nov=True,
                   do_tag=True
                   )

    response.sort_papers('tag')
    response.render_title_precise(request.args['date'], old_date_tmp, new_date_tmp)

    # lists are required at front-end as there is an interface to add paper to any one
    lists = get_lists_for_user()
    response.lists = lists

    return jsonify(response.to_dict())


@main_bp.route('/about')
def about():
    """About page."""
    if current_user.is_authenticated:
        session['pref'] = loads(current_user.pref)
    return render_template('about.jinja2',
                           data=default_data()
                           )


@main_bp.route('/bookshelf')
@login_required
def bookshelf():
    """Bookshelf page."""
    # if list is not specified take the default one
    try:
        display_list = int(request.args.get('list_id'))
    except (ValueError, TypeError):
        fst_list = PaperList.query.filter_by(user_id=current_user.id
                                             ).order_by(PaperList.order).first()
        if not fst_list:
            new_default_list(current_user.id)
            fst_list = PaperList.query.filter_by(user_id=current_user.id
                                                 ).order_by(PaperList.order).first()
        return redirect(url_for(ROOT_BOOK, list_id=fst_list.id))

    try:
        page = int(request.args.get('page'))
    except (ValueError, TypeError):
        return redirect(url_for(ROOT_BOOK,
                                list_id=display_list,
                                page=1))

    lists = get_lists_for_user()
    # if User tries to access the list that doesn't belong to him
    if display_list not in {user_list['id'] for user_list in lists}:
        logging.warning('%r tries to access list %r', current_user.id, display_list)
        return redirect(url_for(ROOT_BOOK, list_id=lists[0]['id']), code=303)

    # get the particular paper list to access papers from one
    paper_list = PaperList.query.filter_by(id=display_list).first()

    # too large page argument
    if page > len(paper_list.papers) / PAPERS_PAGE + 1:
        return redirect(url_for(ROOT_BOOK, list_id=lists[0]['id'], page=1), code=303)

    # reset number of unseen papers
    paper_list.not_seen = 0
    db.session.commit()

    response = PaperResponse()

    # read the papers
    sorted_papers = sorted(paper_list.papers,
                           key=lambda p: p.date_up,
                           reverse=True
                           )
    response.papers = [PaperInterface.from_paper(paper)
                       for paper in sorted_papers[PAPERS_PAGE * (page - 1):][:PAPERS_PAGE]]

    total_pages = len(paper_list.papers) // PAPERS_PAGE
    total_pages += 1 if len(paper_list.papers) % PAPERS_PAGE else 0

    # tag papers
    tags_db = Tag.query.filter_by(user_id=current_user.id).order_by(Tag.order).all()
    tags_inter = [TagInterface.from_tag(tag) for tag in tags_db]
    process_papers(response,
                   tags_inter,
                   current_user.arxiv_cat,
                   do_nov=False,
                   do_tag=True
                   )

    response.sort_papers()
    response.lists = lists
    tags_list = [tag.to_front() for tag in tags_inter]

    url_base = url_for(ROOT_BOOK, list_id=display_list) + '&page='

    return render_template('bookshelf.jinja2',
                           papers=response.to_dict(),
                           title=paper_list.name,
                           url_base=url_base,
                           page=page,
                           paper_page=PAPERS_PAGE,
                           total_pages=total_pages,
                           displayList=display_list,
                           tags=dumps(tags_list),
                           data=default_data()
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
    # create a new one
    if not paper:
        logging.error('Paper is not in the paper table %r', paper_id)
        return dumps({'success': False}), 422

    list_id = request.form.get('list_id')
    paper_list = PaperList.query.filter_by(id=list_id).first()
    if not paper_list:
        logging.error('List is not in the DB %r', list_id)
        return dumps({'success': False}), 422

    lists = get_lists_for_user()
    # if User tries to access the list that doesn't belong to him
    if paper_list.id not in {user_list['id'] for user_list in lists}:
        logging.warning('%r tries to add bm to list %r', current_user.id, paper_list.id)
        return dumps({'success': False}), 422

    # check if paper is already in the given list of the current user
    result = db.session.query(paper_associate).filter_by(list_ref_id=paper_list.id,
                                                         paper_ref_id=paper.id
                                                         ).first()
    if result:
        return dumps({'success': True}), 200

    paper_list.papers.append(paper)
    db.session.commit()
    return dumps({'success': True}), 201


@main_bp.route('/del_bm', methods=['POST'])
@login_required
def del_bm():
    """Delete bookmark."""
    paper_id = request.form.get('paper_id')
    list_id = request.form.get('list_id')
    paper = Paper.query.filter_by(paper_id=paper_id).first()
    if not paper:
        return dumps({'success': False}), 204
    paper_list = PaperList.query.filter_by(id=list_id).first()

    paper_list.papers.remove(paper)
    db.session.commit()
    return dumps({'success': True}), 201


@main_bp.route('/public_tags', methods=['GET'])
@login_required
def public_tags():
    """Get publicly available tags as examples."""
    tags = Tag.query.filter_by(public=True).order_by(Tag.name)
    tag_list = [TagInterface.from_tag(tag).to_name_and_rule() for tag in tags]
    unique_tags = []
    for tag in tag_list:
        if tag not in unique_tags:
            unique_tags.append(tag)

    return jsonify(unique_tags)


@main_bp.route('/feedback', methods=['POST'])
@login_required
def collect_feedback():
    """Send feedback by email to the admin."""
    sender = current_user.email if current_user.email else current_user.orcid
    text = request.form.get('body')

    body = f'Feedback from {sender}\n\n'
    body += text

    msg = Message(body=body,
                  sender="noreply@arxivtag.tk",
                  recipients=['arxivtag@arxivtag.tk'],
                  subject="arXiv tag feedback"
                  )

    mail.send(msg)

    return dumps({'success': True}), 200


@main_bp.route('/test_tag', methods=['GET'])
@login_required
def test_tag():
    """Test the tag rule for some paper data."""
    authors = []
    if request.args.get('author'):
        authors = [au for au in request.args.get('author').split(',')]
    paper = PaperInterface.for_tests(request.args.get('title') if request.args.get('title') else '',
                                     authors,
                                     request.args.get('abs') if request.args.get('abs') else '')

    if not request.args.get('rule'):
        logging.error('Test tag request w/o rule')
        return dumps({'success': False}), 422

    if tag_suitable(paper, request.args.get('rule')):
        return dumps({'result': True}), 200

    return dumps({'result': False}), 200


def update_recent_papers(announce_date: datetime):
    """
    Update "seen" days.

    1. Shift the "last visit day" to the current date.
    2. Shift the bit map with "seen" papers accordingly.
    """
    if not isinstance(current_user.recent_visit, int):
        current_user.recent_visit = 0
        db.session.commit()
        return
    login = current_user.login.replace(tzinfo=timezone.utc)
    delta = (announce_date.date() - login.date()).days
    if delta < 0:
        return
    # shift according to delta since last visit
    current_user.recent_visit = current_user.recent_visit << delta
    # keep only last 7 days
    current_user.recent_visit = current_user.recent_visit % 2 ** RECENT_PAPER_RANGE
    current_user.login = announce_date.replace(tzinfo=None)
    db.session.commit()
