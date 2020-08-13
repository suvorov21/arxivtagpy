from os import path
from datetime import datetime, timedelta
import json
from time import sleep

# server side
from flask import Flask, request, jsonify, send_from_directory, render_template, Markup, redirect
from flask_cors import CORS

# interface with arXiv API
import requests
import feedparser

# utils
from arXivTag.utils.parsers import parse_title, parse_links, parse_authors, parse_cats, tag_suitable
# renders
from arXivTag.utils.render import render_cats, cut_author, render_tags

app = Flask(__name__, instance_relative_config=True)
# read configuration
app.config.from_pyfile('config.py')
conf_file = path.join(app.instance_path, 'settings.cfg')
with open(conf_file) as file:
    settings = json.load(file)

if 'categories' not in settings or 'tags' not in settings:
    raise ValueError(f'Wrong configuration file {conf_file}')

if not isinstance(settings['categories'], list) or \
   len(settings['categories']) == 0 or \
   not isinstance(settings['tags'], list):
    raise ValueError(f'Wrong configuration file {conf_file}')

app.config['CATS'].extend(settings['categories'])
app.config['TAGS'].extend(settings['tags'])

app.config['LAST_VISIT'] = datetime.strptime(settings['last_visit'],
                                             '%Y-%m-%dT%H:%M:%S')
app.config['LAST_PAPER'] = datetime.strptime(settings['last_paper'],
                                             '%Y-%m-%dT%H:%M:%S')
app.config['PARSE_TEX'] = bool(settings['parse_tex'])

CORS(app)

# arXiv API
# params = {'start': 0,
#           'max_results': 1,
#           # hep-ex | hep-ph | physics.ins-det etc.
#           'search_query': 'hep-ex',
#           # relevance | submittedDate | lastUpdatedDate
#           'sortBy': 'submittedDate',
#           # descending | ascending
#           'sortOrder': 'descending'
#         }

@app.errorhandler(500)
def page_not_found(err=500):
    """Error handler.

    raise when arXiv returns not 200.
    """
    app.logger.error('arXiv return != 200.')
    return "<h1>500</h1><p>The resource could not be found.</p>", err

@app.errorhandler(501)
def bad_request(err=501):
    """
    Error handler.

    raise when arXiv doesnt return papers, but error.
    """
    app.logger.error('arXiv return no papers')
    return "<h1>501</h1><p>Bad request syntax.</p>", err

@app.errorhandler(502)
def bad_flask_request(err=502):
    """
    Error handler.

    raise when arXiv doesnt return papers, but error.
    """
    app.logger.error('bad request to flask server')
    return "<h1>502</h1><p>Bad request syntax.</p>", err

def get_papers_in_range(start_date=None, end_date=None,
                        skip_latest=False,
                        **kwargs
                        ):
    """Get papers in date range."""
    query = kwargs['query'] if kwargs.get('sort') is not None else ''
    sort = kwargs['sort'] if kwargs.get('sort') is not None else 'lastUpdatedDate'
    order = kwargs['order'] if kwargs.get('order') is not None else 'descending'

    params = {'start': 0,
              'max_results': app.config['REQUEST_PAPERS'],
              'search_query': query,
              'sortBy': sort,
              'sortOrder': order
              }

    submit = params['sortBy'] == 'submittedDate'

    # loop back until the end_date
    last_paper_date = datetime.today()
    start_id = 0
    if skip_latest:
        if abs(end_date - last_paper_date).days > 4:
            params['max_results'] = 800
        while end_date > last_paper_date:
            if start_id > 30000:
                raise TimeoutError("End date is too far away in the past")
            params['start'] = start_id
            response = get_arxiv(params)
            if response.status_code != 200:
                return 404
            feed = feedparser.parse(response.text)
            if len(feed.entries) == 0:
                return 400

            last_paper_date = get_date(feed.entries[params['max_results']-1],
                                       submit)

            if last_paper_date > end_date:
                start_id += params['max_results']
                # arXiv API is required to be requested with delay
                sleep(2)
                continue

            for entry in feed.entries:
                start_id += 1
                last_paper_date = get_date(entry,
                                           submit)

                if last_paper_date < end_date:
                    break
            break

    # download the papers
    papers = []
    params['start'] = start_id
    if abs(last_paper_date - start_date).days > 4:
        params['max_results'] = 800
    while start_date < last_paper_date:
        response = get_arxiv(params)
        if response.status_code != 200:
            return 404
        feed = feedparser.parse(response.text)
        # Durty fix to test with local data TODO
        # with open("../data/xml_example.xml") as resp_file:
        #     data = resp_file.read()
        # feed = feedparser.parse(data)
        if len(feed.entries) == 0:
            return 400
        for entry in feed.entries:
            last_paper_date = get_date(entry,
                                       submit)

            if last_paper_date < start_date:
                return papers

            paper = {'title': parse_title(entry.title),
                     'author': parse_authors(entry.authors),
                     'date_sub': datetime.strptime(entry.published,
                                                   '%Y-%m-%dT%H:%M:%SZ'
                                                   ),
                     'date_up': datetime.strptime(entry.updated,
                                                  '%Y-%m-%dT%H:%M:%SZ'
                                                  ),
                     'abstract': entry.summary,
                     'pdf': parse_links(entry.links, link_type='pdf'),
                     'abs': parse_links(entry.links, link_type='abs'),
                     'primary': entry.tags[0]['term'],
                     'cats': parse_cats(entry.tags),
                     'tags': [],
                     'cross': False,
                     'up': False
                     }

            papers.append(paper)
        params['start'] += params['max_results']
        # arXiv API is required to be requested with delay
        sleep(2)

    return papers

@app.route('/data', methods=['GET'])
def data():
    """
    Get paper for date.

    return JSON with papers and counters.
    """
    date_dict = {'today': 1, 'week': 2, 'month': 3}

    if 'date' in request.args:
        date_type = date_dict.get(request.args['date'])
    else:
        return bad_request()

    cats_query = r'%20OR%20'.join(f'cat:{cat}' for cat in app.config['CATS'])

    params = {'start': 0,
              'max_results': 1,
              'search_query': cats_query,
              'sortBy': 'lastUpdatedDate',
              'sortOrder': 'descending'
             }

    if 'search_query' in request.args:
        params['search_query'] = request.args['search_query']

    if 'sort_by' in request.args:
        params['sortBy'] = request.args['sortBy']

    today_date = get_today_paper_date(params)

    # TODO think about reference to the real date
    # not the latest published
    if date_type == 1:
        # look at the results of current date
        # last_submission_day - 1 day at 18:00Z
        old_date = today_date - timedelta(days=1)
    elif date_type == 2:
        # if last paper is published on Friday
        # "this week" starts from next Monday
        if (today_date.weekday() == 4):
            old_date = today_date - timedelta(days=1)
        else:
            old_date = today_date - timedelta(days=today_date.weekday()+4)
    elif date_type == 3:
        old_date = today_date - timedelta(days=today_date.day)
    else:
        old_date = app.config['LAST_PAPER']
        app.config['LAST_PAPER'] = today_date
        app.config['LAST_VISIT'] = datetime.now()
        change_settings_file(reload_page=False)


    # over weekend cross
    if old_date.weekday() > 4 and date_type != 4:
        old_date = old_date - timedelta(days=old_date.weekday()-4)

    # papers are submitted by 18:00Z
    if date_type != 4:
        old_date = old_date.replace(hour=17, minute=59, second=59)

    app.logger.info(f'Last paper date {today_date}')
    app.logger.info(f'Collect all papers since {old_date}')

    # Get papers
    par = {'query': params['search_query'],
           'sort': params['sortBy'],
           'order': 'descending'}
    papers = get_papers_in_range(old_date, today_date, skip_latest=False,
                                 **par)

    if papers == 501:
        return bad_request()

    if papers == 500:
        return page_not_found()

    # process papers
    # 1. find
    #   a. cross-refs
    #   b. updated papers
    # 2. process tags
    # 3. cut authors

    n_new, n_cross, n_up = 0, 0, 0
    n_cats = [0 for cat in app.config['CATS']]
    n_tags = [0 for tag in app.config['TAGS']]
    for paper in papers:
        # 1.a count cross-refs
        for cat in paper['cats']:
            # increase cat counter
            if cat in app.config['CATS']:
                n_cats[app.config['CATS'].index(cat)] += 1
            # check if cross-ref
            if cat not in app.config['CATS'] and paper['cats'][0] not in app.config['CATS']:
                n_cross += 1 if not paper['cross'] else 0
                paper['cross'] = True

        # 1.b count updated papers
        if paper['date_sub'] < old_date:
            paper['up'] = True
            n_up += 1

        if not paper['up'] and not paper['cross']:
            n_new += 1

        # 2.
        for num, tag in enumerate(app.config['TAGS']):
            if tag_suitable(paper, tag['rule']):
                paper['tags'].append(num)
                n_tags[num] += 1

        # 3. cut author list
        paper['author'] = cut_author(paper['author'], app.config['N_AUTHORS'])

        # app.logger.debug(f'Paper: {paper["title"]}')
        # app.logger.debug(f'cross: {paper["cross"]}')
        # app.logger.debug(f'updat: {paper["up"]}')

    content = {'n_new': n_new,
               'n_cross': n_cross,
               'n_up': n_up,
               'n_cat': n_cats,
               'n_tag': n_tags,
               'tags': app.config['TAGS'],
               'papers': papers
               }

    return jsonify(content)

@app.route('/')
def root():
    """
    Get paper for date.

    options: 1. today, 2. week, 3. month.
    """
    date_dict = {'today': 1, 'week': 2, 'month': 3, 'last': 4}

    if 'date' in request.args:
        date_type = date_dict.get(request.args['date'])
    else:
        return redirect("/?date=today", code=302)
    if date_type is None:
        return bad_request()

    today_date = datetime.today()

    if date_type == 1:
        title = 'Papers for today: ' + today_date.strftime('%d %B %Y')

    elif date_type == 2:
        title = 'Papers for this week: ' + \
                (datetime.today() - \
                timedelta(days=today_date.weekday())).strftime('%d %B %Y') + \
                ' - ' + \
                (datetime.today() + \
                timedelta(days=6-today_date.weekday())).strftime('%d %B %Y')

    elif date_type == 3:
        title = 'Papers for this month: ' + datetime.today().strftime('%B %Y')

    else:
        title = 'Papers since last visit on ' + \
                app.config['LAST_VISIT'].strftime('%d %B %Y')

    # Fill the HTML template with title, categories and tags
    title = Markup(title)
    categories = Markup(render_cats(app.config['CATS']))
    tags = Markup(render_tags(app.config['TAGS']))

    return render_template('index.html',
                           title=title,
                           categories=categories,
                           tags=tags,
                           last_visit=app.config['LAST_VISIT'].strftime('%d %B %Y'),
                           parse_TeX=app.config['PARSE_TEX']
                           )

@app.route('/add_cat')
def add_cat():
    """Add category."""
    if 'fcat' in request.args:
        app.config['CATS'].append(request.args['fcat'])
    else:
        return bad_flask_request()

    return change_settings_file()

@app.route('/rm_cat')
def rm_cat():
    """Remove a category."""
    if 'fcat' in request.args:
        app.config['CATS'].remove(request.args['fcat'])
    else:
        return bad_flask_request()

    return change_settings_file()


@app.route('/add_tag')
def add_tag():
    """Add tag."""
    tag = {'name': request.args['tag_name'],
           'rule': request.args['tag_rule'],
           'color': request.args['tag_color']}
    order = int(request.args['tag_order'])

    app.config['TAGS'].insert(order, tag)

    return change_settings_file()

@app.route('/edit_tag')
def edit_tag():
    """Edit tag."""
    # remove tag
    if request.args['action'] == 'delete':
        name = request.args['tag_name']
        app.config['TAGS'] = [tag for tag in app.config['TAGS'] if tag['name'] != name]
        return change_settings_file()

    # change tag properties
    tag_id = int(request.args['ftag_id'])
    app.config['TAGS'][tag_id]['name'] = request.args['tag_name']
    app.config['TAGS'][tag_id]['rule'] = request.args['tag_rule']
    app.config['TAGS'][tag_id]['color'] = request.args['tag_color']

    # change tag order
    # not very elegant though... TODO
    new_id = int(request.args['tag_order'])
    if new_id != tag_id:
        tag = {'name': app.config['TAGS'][tag_id]['name'],
               'rule': app.config['TAGS'][tag_id]['rule'],
               'color': app.config['TAGS'][tag_id]['color']}
        app.config['TAGS'].pop(tag_id);
        app.config['TAGS'].insert(new_id, tag)

    return change_settings_file()

@app.route('/set_tex')
def set_tex():
    if 'tex' not in request.args:
        return bad_flask_request()

    if request.args['tex'] not in ('on', 'off'):
        return bad_flask_request()

    app.config['PARSE_TEX'] = True if request.args['tex'] == 'on' else False

    return change_settings_file()



def change_settings_file(reload_page=True):
    """Change setting file.

    Store new categories, tags, last visit dates
    in the configuration file.
    """
    new_settings = {'categories': app.config['CATS'],
                    'tags': app.config['TAGS'],
                    'last_visit': app.config['LAST_VISIT'].strftime('%Y-%m-%dT%H:%M:%S'),
                    'last_paper': app.config['LAST_PAPER'].strftime('%Y-%m-%dT%H:%M:%S'),
                    'parse_tex': app.config['PARSE_TEX']
                    }

    new_conf_file = path.join(app.instance_path, 'settings.cfg')
    with open(new_conf_file, 'w') as new_file:
        new_file.write(json.dumps(new_settings, indent=4))

    if reload_page:
        return redirect("/?date=today", code=302)
    return True

def get_today_paper_date(params):
    """Get the latest paper and extract date."""
    backup = params['sortBy']
    params['sortBy'] = 'submittedDate'
    response = get_arxiv(params)
    params['sortBy'] = backup
    if response.status_code != 200:
        return page_not_found()
    feed = feedparser.parse(response.text)
    if len(feed.entries) == 0:
        return bad_request()

    return get_date(feed.entries[0])

def get_date(entry, submit=True):
    """Get the date from the paper."""
    if submit:
        last_date_str = entry.published
    else:
        last_date_str = entry.updated

    return datetime.strptime(last_date_str,
                             '%Y-%m-%dT%H:%M:%SZ'
                             )

def get_arxiv(params):
    """Arxiv API request logging."""
    response = requests.get(app.config['ARXIV_URL'], params)
    app.logger.info(f'GET arXiv: {response.url}')
    return response

@app.route('/favicon.ico')
def favicon():
    """icon."""
    return send_from_directory(path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

def run():
    """Start server."""
    try:
        app.run(port=app.config['PORT'], host=app.config['HOST'])
    except OSError:
        print(f'The adress {app.config["HOST"]}:{app.config["PORT"]} is likely in use.')
        print('1. Check that this particular app is not in progress.')
        print('2. If not, your system may use this adress for other purpose. Change the port in config.py')

if __name__ == '__main__':
    run()
