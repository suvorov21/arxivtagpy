"""
Papers parsers utils.

Paper downloader function update the paper DB.
Tag processor checks if a given paper is suitable with the tag
"""

from typing import Dict, Tuple
from re import search, compile, sub, IGNORECASE
from datetime import datetime, timedelta
import logging

from .model import db, Paper
from .paper_api import ArxivOaiApi, get_date_range, get_arxiv_sub_start

rule_dict = {'ti': 'title',
             'au': 'author',
             'abs': 'abstract',
             'cat': 'cats'
             }

def update_papers(api_list: list, **kwargs):
    """
    Update paper table.

    Get papers from all API with download_papers()
    and store in the DB.
    """
    updated = 0
    downloaded = 0
    read = 0

    n_papers = kwargs.get('n_papers')
    last_paper_date = kwargs['last_paper_date']

    for api in api_list:
        for paper in api.download_papers():

            # stoppers
            if n_papers and read > n_papers:
                break

            # too old paper. Skip
            if paper.date_up < last_paper_date:
                continue

            paper_prev = Paper.query.filter_by(
                            paper_id=paper.paper_id
                            ).first()

            if paper_prev:
                if kwargs.get('do_update'):
                    update_paper_record(paper_prev, paper)
                    updated += 1
            else:
                db.session.add(paper)
                downloaded += 1
            read += 1
            if read % api.COMMIT_PERIOD == 0:
                logging.info('read %i papers', read)
                db.session.commit()

    db.session.commit()

    logging.info('Paper update done: %i new; %i updated',
                 downloaded,
                 updated
                 )



def update_paper_record(paper_prev: Paper, paper: Paper):
    """Update the paper record."""
    paper_prev.title = paper.title
    paper_prev.date_up = paper.date_up
    paper_prev.author = paper.author
    paper_prev.doi = paper.doi
    paper_prev.version = paper.version
    paper_prev.abstract = paper.abstract
    paper_prev.cats = paper.cats

def resolve_doi(doi: str) -> str:
    """Resolve doi string into link."""
    return 'https://www.doi.org/' + doi

def render_paper_json(paper: Paper) -> Dict:
    """Render Paper class obkect into JSON for front-end."""
    result = {'id': paper.paper_id,
              'title': paper.title,
              'author': paper.author,
              'date_sub': paper.date_sub,
              'date_up': paper.date_up,
              'abstract': paper.abstract,
              'cats': paper.cats,
              # to be filled later in process_papers()
              'tags': [],
              'nov': 0
              }
    if paper.source == 1:
        result['ref_pdf'] = ArxivOaiApi().get_ref_pdf(paper.paper_id,
                                                      paper.version
                                                      )
        result['ref_web'] = ArxivOaiApi().get_ref_web(paper.paper_id,
                                                      paper.version
                                                      )

    if paper.doi is not None:
        result['ref_doi'] = resolve_doi(paper.doi)

    return result


def process_papers(papers: Dict,
                   tags: Dict,
                   cats: Tuple[str],
                   do_nov: bool,
                   do_tag: bool
                   ) -> Dict:
    """
    Papers processing.

    Process:
    1. novelty. use 'bit' map
        0 - undef 1 - new, 2 - cross, 4 - up
        a. cross-ref
        b. updated
    2. categories
    3. process tags
    """
    papers['n_nov'] = [0] * 3
    papers['n_cats'] = [0] * len(cats)
    papers['n_tags'] = [0] * len(tags)
    for paper in papers['papers']:
        if do_nov:
            # count paper per category
            for cat in paper['cats']:
                if cat in cats:
                    papers['n_cats'][cats.index(cat)] += 1
            # 1.a check if cross-ref
            if paper['cats'][0] not in cats:
                papers['n_nov'][1] += 1
                paper['nov'] += 2

            # 1.b count updated papers
            if paper['date_sub'] < papers['last_date']:
                paper['nov'] += 4
                papers['n_nov'][2] += 1

            if paper['nov'] == 0:
                paper['nov'] = 1
                papers['n_nov'][0] += 1

        # 2.
        if do_tag:
            for num, tag in enumerate(tags):
                if tag_suitable(paper, tag['rule']):
                    paper['tags'].append(num)
                    papers['n_tags'][num] += 1
    return papers


def tag_suitable(paper: Dict, rule: str) -> bool:
    """
    Simple rules are expected in the most of th cases.

    1. Find logic AND / OR outside curly and round brackets
    2. If no - parse rules inside curly brackets
    3. OR: and process rule parts one by one separated by |
    return True at first true condition
    return False if no matches
    4. AND: process rule parts separated by &
    return False at first false match
    return True if no false matches

    :param      paper:       The paper
    :type       paper:       Dict
    :param      rule:        The rule
    :type       rule:        str

    :returns:   if the paper suits the tag
    :rtype:     bool
    """
    # remove parentheses if the whole rule is inside
    if rule[0] == '(' and rule[-1] == ')':
        rule = rule[1:-1]

    brackets = 0
    or_pos, and_pos = [], []
    for pos, char in enumerate(rule):
        if char in ['(', '{']:
            brackets += 1
            continue
        if char in [')', '}']:
            brackets -= 1
            continue
        if brackets == 0:
            if char == '|':
                or_pos.append(pos)
            elif char == '&':
                and_pos.append(pos)

    # if no AND/OR found outside brackets process a rule inside curly brackets
    if len(and_pos) == 0 and len(or_pos) == 0:
        return parse_simple_rule(paper, rule)

    # add rule length limits
    or_pos.insert(0, -1)
    or_pos.append(len(rule))

    # process logic OR
    if len(or_pos) > 2:
        for num, pos in enumerate(or_pos[:-1]):
            if tag_suitable(paper, rule[pos+1:or_pos[num+1]]):
                return True

    # if logic OR was found but True was not returned before
    if len(or_pos) > 2:
        return False

    # add rule length limits
    and_pos.insert(0, -1)
    and_pos.append(len(rule))

    # process logic AND
    if len(and_pos) > 2:
        for num, pos in enumerate(and_pos[:-1]):
            if not tag_suitable(paper, rule[pos+1:and_pos[num+1]]):
                return False

    # if logic AND is inside the rule but False was not found
    if len(and_pos) > 2:
        return True

    # default safety return
    return False

def parse_simple_rule(paper: Dict, condition: str) -> bool:
    """Parse simple rules as ti/au/abs."""
    prefix_re = search(r'^(ti|abs|au|cat)\{(.*?)\}', condition)
    if not prefix_re:
        return False

    prefix = prefix_re.group(1)
    condition = prefix_re.group(2)

    if prefix not in rule_dict:
        logging.error('Prefix is unknown %r', prefix)

    search_target = paper[rule_dict[prefix]]
    # in case of
    # 1. author
    # 2. Paper category
    #  the target is a list
    # join the list into string
    if isinstance(search_target, list):
        target = paper['author' if prefix == 'au' else 'cats']
        search_target = ', '.join(target)

    # cast logic AND to proper REGEX
    if '&' in condition:
        cond_list = condition.split('&')
        condition = '(' + condition.replace('&', '.*')
        condition += ')|('
        condition += '.*'.join(cond_list[::-1]) + ')'

    # escape backslash for proper treatment of TeX expressions
    # in the DB TeX formulas are stored with one slash
    # wile re requires escape \ before the TeX one
    condition = condition.replace('\\', '\\\\')

    # do search among separate words only. 
    # But ignore this for TeX
    condition = sub(r'(^\b|\|\b|\(\b)', r'\1\\b', condition)

    # inversion of the rule
    inversion = False
    if '!' in condition:
        condition = condition.replace('!', '')
        inversion = True

    
    re_cond = compile(condition,
                      flags=IGNORECASE
                      )

    found = re_cond.search(search_target) is not None

    if  found != inversion:
        return True
    return False

def get_json_papers(cats: list,
                    old_date: datetime,
                    new_date: datetime
                    ) -> dict:
    """Get list of papers from DB in JSON format."""
    paper_query = Paper.query.filter(
                        Paper.cats.overlap(cats),
                        Paper.date_up > old_date,
                        Paper.date_up < new_date,
                        ).order_by(Paper.date_up.desc()).all()
    return [render_paper_json(paper) for paper in paper_query]

def get_json_unseen_papers(cats: list,
                           recent_visit: int,
                           recent_range: int,
                           announce_date: datetime
                           ) ->dict:
    """Get unseen papers from DB in JSON format."""
    result = []
    for i in range(recent_range - 1):
        if not 2**i & recent_visit:
            # current_user.recent_visit = current_user.recent_visit | 2**i
            old_date_tmp, new_date_tmp, new_date =get_date_range(
                                'today',
                                announce_date - timedelta(days=i)
                                )
            old_date = get_arxiv_sub_start(old_date_tmp.date())
            paper_query = Paper.query.filter(
                        Paper.cats.overlap(cats),
                        Paper.date_up > old_date,
                        Paper.date_up < new_date,
                        ).order_by(Paper.date_up.desc()).all()
            result.extend([render_paper_json(paper) for paper in paper_query])
    return result