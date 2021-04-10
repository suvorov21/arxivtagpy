"""Papers parsers and donwnload API."""

from os import linesep
from time import sleep
from datetime import datetime
from typing import Dict, Tuple, List
from re import search, IGNORECASE
import logging
from random import randrange

from feedparser import parse
from requests import get

from .model import Paper

rule_dict = {'ti': 'title',
             'au': 'author',
             'abs': 'abstract'
             }


class PaperApi:
    """API default class."""

    def_params = {}
    delay = 0
    URL = ""
    last_paper = datetime.now()

class ArxivApi(PaperApi):
    """API for arXiv connection."""

    def_params = {'start': 0,
                  'max_results': 500,
                  'search_query': 'all:a',
                  'sortBy': 'lastUpdatedDate',
                  'sortOrder': 'descending'
                 }

    URL = 'http://export.arxiv.org/api/query'
    delay = 30
    verbose = False
    max_papers = 100000
    last_paper_id = '000'
    max_attempt_to_fail = 10

    def __init__(self, params: Dict, **kwargs):
        """Initialise arXiv API."""
        self.params = ArxivApi.def_params
        self.params.update(params)
        self.last_paper = kwargs.get('last_paper')
        self.last_paper_id = kwargs.get('last_paper_id')

    def get_papers(self, **kwargs) -> List:
        """Download papers and return a list of Papers models."""
        if 'last_paper' in kwargs:
            self.last_paper = kwargs.get('last_paper')
        if 'last_paper_id' in kwargs:
            self.last_paper_id = kwargs.get('last_paper')
        if 'n_papers' in kwargs:
            self.max_papers = kwargs.get('n_papers')
            if self.max_papers < self.params['max_results']:
                self.params['max_results'] = self.max_papers
        if 'search_query' in kwargs:
            self.params['search_query'] = kwargs.get('search_query')

        papers = []
        fail_attempts = 0

        if ArxivApi.verbose:
            logging.debug('Start download')

        while True:
            response = get(self.URL, self.params)

            if ArxivApi.verbose:
                logging.debug(response.url)

            if response.status_code != 200:
                return 404

            # parse arXiv response
            feed = parse(response.text)
            if len(feed.entries) != self.params['max_results']:
                logging.warning("Got %i results from %i. Retrying.",
                                len(feed.entries),
                                self.params['max_results'])
                fail_attempts += 1
                if fail_attempts > self.max_attempt_to_fail:
                    logging.error('Download exceeds max fail attempts')
                    return None
                sleep(randrange(120, 200))
                continue

            for entry in feed.entries:
                date = datetime.strptime(entry.updated,
                                         '%Y-%m-%dT%H:%M:%SZ'
                                         )
                paper_id = entry.id.split('/')[-1]
                paper_id = paper_id.split('v')[0]

                if ArxivApi.verbose:
                    logging.debug('#%i date: %s id = %s',
                                  len(papers),
                                  entry.updated,
                                  paper_id
                                  )
                if date < self.last_paper \
                    or paper_id == self.last_paper_id \
                    or len(papers) >= self.max_papers:
                    break

                papers.append(Paper(
                    title=fix_xml(entry.title),
                    author=parse_authors(entry.authors),
                    date_sub=datetime.strptime(entry.published,
                                                   '%Y-%m-%dT%H:%M:%SZ'
                                                   ),
                    date_up=date,
                    abstract=fix_xml(entry.summary),
                    ref_pdf=parse_links(entry.links, link_type='pdf'),
                    ref_web=parse_links(entry.links, link_type='abs'),
                    ref_doi=parse_links(entry.links, link_type='doi'),
                    paper_id=paper_id,
                    cats=parse_cats(entry.tags)
                    ))

            if date < self.last_paper \
                or paper_id == self.last_paper_id:
                break

            if len(papers) >= self.max_papers:
                break

            # delay for a next request
            sleep(randrange(40, 80))
            self.params['start'] += self.params['max_results']

        return papers

def fix_xml(xml: str) -> str:
    """
    Parse xml tag content!

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
    Loop over links and extract hrefs to pdf and arXiv abstract!

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
        condition += ')|('
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
