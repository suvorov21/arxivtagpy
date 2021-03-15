from datetime import datetime
from json import loads, dumps

from flask import Blueprint, render_template, flash, session, redirect, \
url_for, request, jsonify
from flask_login import current_user, login_required

from .model import db, Paper, PaperList, tags
from .render import render_papers, render_title
from .papers import ArxivApi, process_papers

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
        # WARNING a dirty fix to get rid of /flask/flask.wsgi in the adress bar
        if 'arxivtag' in request.headers['Host'] :
            # if production, go 3 levels up
            return redirect('../../../papers?date=today')
        else:
            # not a production (local/heroku) let flask care about path
            return redirect(url_for('main_bp.papers_list', date='today'))


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
                           math_jax=True if session['pref'].get('tex') else False
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
    load_prefs()
    cats_query = r'%20OR%20'.join(f'cat:{cat}' for cat in session['cats'])
    paper_api = ArxivApi({'search_query': cats_query},
                         last_paper=current_user.last_paper
                         )
    # further code is paper source independent.
    # Any API can be defined above
    papers = paper_api.get_papers(date_type,
                                  last_paper=current_user.last_paper
                                  )

    # error hahdler
    if isinstance(papers, int):
        return dumps({'success':False}), papers

    # store the info about last checked paper
    # descending paper order is assumed
    if len(papers['content']) > 0 and papers['content'][0].get('date_up'):
        # update the date of last visit
        current_user.login = datetime.now()
        current_user.last_paper = papers['content'][0]['date_up']
        db.session.commit()

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
    page = 'cat'
    if 'page' in request.args:
        page = request.args['page']
    # TODO this is excessive
    # CATS and TAGS are send back for all the settings pages
    return render_template('settings.jinja2',
                           cats=session['cats'],
                           tags=session['tags'],
                           # TODO read from prefs
                           pref=dumps(session['pref']),
                           math_jax=True if session['pref'].get('tex') else False,
                           page=page
                           )

@main_bp.route('/about')
def about():
    """About page."""
    return render_template('about.jinja2')


def load_prefs():
    """Load preferences from DB to session."""
    # if 'cats' not in session:
    session['cats'] = current_user.arxiv_cat

    # read tags
    # if 'tags' not in session:
    session['tags'] = loads(current_user.tags)


    # read preferences
    # if 'pref' not in session:
    if "NoneType" not in str(type(current_user.pref)):
        session['pref'] = loads(current_user.pref)


########### Setings change##############################################


@main_bp.route('/mod_cat', methods=['POST'])
@login_required
def mod_cat():
    """Apply category changes."""
    new_cat = []
    new_cat = request.form.getlist("list[]")

    current_user.arxiv_cat = new_cat
    db.session.commit()
    # WARNING Do I really need prefs in session
    # How much it affect db load?
    session['cats'] = current_user.arxiv_cat
    return dumps({'success':True}), 200

@main_bp.route('/mod_tag', methods=['POST'])
@login_required
def mod_tag():
    """Apply tag changes."""
    new_tags = []
    # Fix key break with ampersand
    for arg in request.form.to_dict().keys():
        new_tags.append(arg)

    new_tags = '&'.join(new_tags)

    if new_tags == '':
        return dumps({'success': False}), 204

    current_user.tags = str(new_tags)
    db.session.commit()
    # WARNING Do I really need prefs in session
    # How much it affect db load?
    session['tags'] = loads(current_user.tags)
    return dumps({'success':True}), 200

@main_bp.route('/mod_pref', methods=['POST'])
@login_required
def mod_pref():
    """Apply preference changes."""
    new_pref = []
    for arg in request.form.to_dict().keys():
        new_pref = arg

    if new_pref == []:
        return dumps({'success': False}), 204

    current_user.pref = str(new_pref)
    db.session.commit()
    # WARNING Do I really need prefs in session
    # How much it affect db load?
    session['pref'] = loads(current_user.pref)
    return dumps({'success':True}), 200


##### Bookshelf stuff ##################################################
@main_bp.route('/add_bm', methods=['POST'])
@login_required
def add_bm():
    """Add bookmark."""
    # read input
    title = request.form.get('title')
    paper_id = request.form.get('paper_id')

    # search if paper is already in the paper DB
    paper = Paper.query.filter_by(paper_id=paper_id).first()
    # if paper is not in the paper table
    # cerate a new one
    if not paper:
        paper = Paper(title=title,
                      paper_id=paper_id
                      )

        db.session.add(paper)

    # in case no list is there
    # create a new one
    # TEMP work with one list for the time beeing
    paper_list = PaperList.query.filter_by(user_id=current_user.id).first()
    if paper_list is None:
        # create a default list
        paper_list = PaperList(name='Favourite',
                               user_id=current_user.id
                               )
        db.session.add(paper_list)

    # check if paper is already in the given list of the current user
    result = db.session.query(tags).filter_by(list_ref_id=paper_list.id,
                                              paper_ref_id=paper.id
                                              ).first()
    if result:
        return dumps({'success':True}), 200

    paper.list_id.append(paper_list)
    db.session.commit()
    print('added')
    return dumps({'success':True}), 201
