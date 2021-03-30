from os import linesep
from time import sleep
from datetime import datetime, timedelta, time
from typing import Dict, Tuple, List
from re import search, IGNORECASE

from feedparser import parse
from requests import get

rule_dict = {'ti': 'title',
             'au': 'author',
             'abs': 'abstract'
             }


class PaperApi:
    """
    API default class.
    """

    def_params = {}
    delay = 0
    URL = ""
    max_papers = 10000
    last_paper = datetime.now()

class ArxivApi(PaperApi):
    """
    API for arXiv connection.
    """

    def_params = {'start': 0,
                  'max_results': 200,
                  'search_query': 'hep-ex',
                  'sortBy': 'lastUpdatedDate',
                  'sortOrder': 'descending'
                 }

    URL = 'http://export.arxiv.org/api/query'
    max_papers = 1000
    delay = 2
    norm_papers = 200
    verbose = False

    def __init__(self, params: Dict, **kwargs):
        """Initialise arXiv API."""
        self.params = ArxivApi.def_params
        self.params.update(params)
        if 'last_paper' in kwargs:
            self.last_paper = kwargs.get('last_paper')

    def get_papers(self, date_type: int, **kwargs) -> Dict:
        """Download papers and return an array of Paper class obj."""
        if date_type == 1:
            self.params['max_results'] = 600
        elif date_type == 2:
            self.params['max_results'] = 900

        response = get(self.URL, self.params)

        if ArxivApi.verbose:
            print(response.url)
            print(response.text)

        if response.status_code != 200:
            return 404

        # parse arXiv response
        feed = parse(response.text)
        if len(feed.entries) == 0:
            return 400

        today_date = datetime.strptime(feed.entries[0].updated,
                                       '%Y-%m-%dT%H:%M:%SZ'
                                       )

        if ArxivApi.verbose:
            print(feed.entries[0].updated, today_date)

        if date_type == 0:
            # look at the results of current date
            # last_submission_day - 1 day at 18:00Z
            old_date = today_date - timedelta(days=1)
        elif date_type == 1:
            # if last paper is published on Friday
            # "this week" starts from next Monday
            if today_date.weekday() == 4:
                old_date = today_date - timedelta(days=1)
            else:
                old_date = today_date - timedelta(days=today_date.weekday()+4)
        elif date_type == 2:
            old_date = today_date - timedelta(days=today_date.day)
        else:
            old_date = kwargs.get('last_paper')

        # over weekend cross
        if old_date.weekday() > 4 and date_type != 4:
            old_date = old_date - timedelta(days=old_date.weekday()-4)

        # papers are submitted by 18:00Z
        if date_type < 3:
            old_date = old_date.replace(hour=17, minute=59, second=59)
        else:
            old_date = datetime.combine(old_date,
                                        time(hour=17, minute=59, second=59))

        if ArxivApi.verbose:
            print('old', old_date)

        papers = {'n_cats': None,
                  'n_nov': None,
                  'n_tags': None,
                  'last_date': old_date,
                  'date_type': date_type,
                  'content': []
                  }

        while True:
            for entry in feed.entries:
                date = datetime.strptime(entry.updated,
                                         '%Y-%m-%dT%H:%M:%SZ'
                                         )
                if ArxivApi.verbose:
                    print(date, len(papers['content']))
                if date < old_date:
                    break

                papers['content'].append(
                    {'title': fix_xml(entry.title),
                     'author': parse_authors(entry.authors),
                     'date_sub': datetime.strptime(entry.published,
                                                   '%Y-%m-%dT%H:%M:%SZ'
                                                   ),
                     'date_up': date,
                     'abstract': fix_xml(entry.summary),
                     'ref_pdf': parse_links(entry.links, link_type='pdf'),
                     'ref_web': parse_links(entry.links, link_type='abs'),
                     'ref_doi': parse_links(entry.links, link_type='doi'),
                     'id': entry.id.split('/')[-1],
                     'primary': entry.tags[0]['term'],
                     'cats': parse_cats(entry.tags),
                     'tags': [],
                     'nov': 0
                    })

            if date <= old_date or len(papers['content']) > 10000:
                break

            # make a next request
            # TODO unify all the requests in one function?
            sleep(self.delay)
            self.params['start'] += self.params['max_results']
            response = get(self.URL, self.params)

            if response.status_code != 200:
                return 404

            # parse arXiv response
            feed = parse(response.text)
            if len(feed.entries) == 0:
                return 400

        return papers

def fix_xml(xml: str) -> str:
    """
    Parse xml tag content

    Remove line endings and double spaces.
    """
    return xml.replace(linesep, " ").replace("  ", " ")

def parse_authors(authors) -> List:
    """Convert authors from freeparser output to list."""
    return [au.name for au in authors]

def parse_cats(cats) -> List:
    """Convert categories from freeparser output to list."""
    return [cat.term for cat in cats]

def parse_links(links, link_type='pdf') -> str:
    """
    Loop over links and extract hrefs to pdf and arXiv abstract

    parse links
    related & title = pdf --> pdf
    related & title = doi --> doi
    alternate --> abstract
    """
    for link in links:
        if link.rel == 'alternate' and link_type == 'abs':
            return link.href
        if link.rel == 'related':
            if link.title == 'pdf' and link_type == 'pdf':
                return link.href
            if link.title == 'doi' and link_type == 'doi':
                return link.href

    return None

def process_papers(papers: Dict,
                   tags: Dict,
                   cats: Tuple[str]
                   ) -> Dict:
    """
    Papers processing

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
    for paper in papers['content']:
        # 1.a count cross-refs
        for cat in paper['cats']:
            # increase cat counter
            if cat in cats:
                papers['n_cats'][cats.index(cat)] += 1
            # check if cross-ref
            if cat not in cats and paper['cats'][0] not in cats:
                papers['n_nov'][1] += 1 if paper['nov'] != 2 else 0
                paper['nov'] = 2

        # 1.b count updated papers
        if paper['date_sub'] < papers['last_date']:
            paper['nov'] = 4
            papers['n_nov'][2] += 1

        if paper['nov'] == 0:
            paper['nov'] = 1
            papers['n_nov'][0] += 1

        # 2.
        for num, tag in enumerate(tags):
            if tag_suitable(paper, tag['rule']):
                paper['tags'].append(num)
                papers['n_tags'][num] += 1
    return papers


def tag_suitable(paper: Dict, rule: str) -> bool:
    """
    Simple rules are expected in the most of th cases,
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
        if char in ['(', '{']: brackets += 1; continue;
        if char in [')', '}']: brackets -= 1; continue;
        if brackets == 0:
            if char == '|':
                or_pos.append(pos)
            elif char == '&':
                and_pos.append(pos)

    # if no AND/OR found outside brackets process a rule inside curly brackets
    if (len(and_pos) == 0 and len(or_pos) == 0):
        return parse_simple_rule(paper, rule)

    # add rule length limits
    or_pos.insert(0, -1)
    or_pos.append(len(rule))

    # process logic OR
    if (len(or_pos) > 2):
        for num, pos in enumerate(or_pos[:-1]):
            if tag_suitable(paper, rule[pos+1:or_pos[num+1]]):
                return True

    # if logic OR was found but True was not returned before
    if (len(or_pos) > 2):
        return False

    # add rule length limits
    and_pos.insert(0, -1)
    and_pos.append(len(rule))

    # process logic AND
    if (len(and_pos) > 2):
        for num, pos in enumerate(and_pos[:-1]):
            if not tag_suitable(paper, rule[pos+1:and_pos[num+1]]):
                return False

    # if logic AND is inside the rule but False was not found
    if (len(and_pos) > 2):
        return True

    # default safety return
    return False

def parse_simple_rule(paper: Dict, condition: str) -> bool:
    """Parse simple rules as ti/au/abs."""
    prefix_re = search(r'^(ti|abs|au)\{(.*?)\}', condition)
    if not prefix_re:
        return False

    prefix = prefix_re.group(1)
    condition = prefix_re.group(2)

    if prefix not in rule_dict:
        raise ValueError('Prefix is unknown')

    search_target = paper[rule_dict[prefix]]
    # in case of author the target is a list
    # join the list into string
    if isinstance(search_target, list):
        search_target = ', '.join(paper['author'])

    # cast logic AND to proper REGEX
    if '&' in condition:
        cond_list = condition.split('&')
        condition = '(' + condition.replace('&', '.*')
        condition +=')|('
        condition += '.*'.join(cond_list[::-1]) + ')'

    # inversion of the rule
    inversion = False
    if '!' in condition:
        condition = condition.replace('!', '')
        inversion = True

    found = search(condition,
                   search_target,
                   flags=IGNORECASE
                   ) is not None

    if  found != inversion:
        return True
    return False
