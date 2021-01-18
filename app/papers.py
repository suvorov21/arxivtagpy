from os import linesep
from time import sleep
from datetime import datetime, timedelta
from typing import Dict, Tuple, List
from re import findall, search, escape, IGNORECASE

from feedparser import parse
from requests import get


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
            # TODO add handler
            return 404

        # parse arXiv response
        feed = parse(response.text)
        if len(feed.entries) == 0:
            # TODO add handler
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
        if date_type != 4:
            old_date = old_date.replace(hour=17, minute=59, second=59)

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
            # print(response.url)

            if response.status_code != 200:
                # TODO add handler
                return 404

            # parse arXiv response
            feed = parse(response.text)
            if len(feed.entries) == 0:
                # TODO add handler
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
                   cats: Tuple[str],
                   easy_and: bool
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
            if tag_suitable(paper, tag['rule'], easy_and):
                paper['tags'].append(num)
                papers['n_tags'][num] += 1
    return papers

def tag_suitable(paper: Dict, rule: str, easy_and: bool) -> bool:
    """
    Check if paper is suitable with a tag rule

    :param      paper:  The paper
    :type       paper:  paper JSON entry
    :param      rule:    The tag rule
    :type       rule:    re rule for tag assignment
    """
    # recursion end
    if rule == 'True':
        return True
    if rule == 'False':
        return False

    rule_outside_curly = ''.join(findall(r'(.*?)\{.*?\}', rule))
    # parse brackets () outtside {}
    if '(' in rule_outside_curly:
        start_pos = search(r"(^|\}[&|])(\()", rule).start(2)
        end_pos = search(r"\}(\))", rule).start(1)
        # start_pos = search(r"(.*?)\{.*?\}", rule).start(2))
        condition = str(tag_suitable(paper, rule[start_pos+1:end_pos], easy_and))
        new_rule = rule[0:start_pos] + condition + rule[end_pos+1:]
        return tag_suitable(paper, new_rule, easy_and)

    # parse logic AND
    # while '&' outside {} exists
    if '&' in rule_outside_curly:
        fst, scd, before_fst, after_scd = separate_rules(rule, '&')
        condition = str(tag_suitable(paper, fst, easy_and) and tag_suitable(paper, scd, easy_and))
        new_rule = before_fst + condition + after_scd
        return tag_suitable(paper, new_rule, easy_and)

    # parse logic OR
    if '|' in rule_outside_curly:
        fst, scd, before_fst, after_scd = separate_rules(rule, '|')
        condition = str(tag_suitable(paper, fst, easy_and) or tag_suitable(paper, scd, easy_and))
        new_rule = before_fst + condition + after_scd
        return tag_suitable(paper, new_rule, easy_and)

    # parse simple conditions ti/abs/au
    res = search(r'^(ti|abs|au)\{.*?\}', rule)
    if res:
        return parse_simple_rule(paper, rule, res.group(1), easy_and)

    return False

def separate_rules(rule: str, sign: str):
    """Split two parts of the rule with sign."""
    sign_pos = search(r"\{.*?\}(%s).*\{.*?\}" % escape(sign),
                      rule).start(1)

    fst = (search(r'.*\{(.*?)(&|\||$)',
                  rule[:sign_pos][::-1]
                  ).group(0))[::-1]

    scd = rule[sign_pos+1:].split('}')[0] + '}'

    fst_start = sign_pos - len(fst)
    scd_end = sign_pos + len(scd)

    return fst, scd, rule[0:fst_start], rule[scd_end+2:]

def parse_simple_rule(paper: Dict, rule: str, prefix: str, easy_and: bool) -> bool:
    """Parse simple rules as ti/au/abs."""
    rule_dict = {'ti': 'title',
                 'au': 'author',
                 'abs': 'abstract'
                 }
    if prefix not in rule_dict:
        raise ValueError('Prefix is unknown')

    condition = search(r'^%s{(.*)}.*' % prefix, rule).group(1)
    search_target = paper[rule_dict[prefix]]
    # in case of author the target is a list
    if isinstance(search_target, list):
        search_target = ', '.join(paper['author'])

    if '&' in condition and easy_and:
        cond_list = condition.split('&')
        condition = '(' + condition.replace('&', '.*')
        condition +=')|('
        condition += '.*'.join(cond_list[::-1]) + ')'

    if search(condition,
              search_target,
              flags=IGNORECASE
              ) is None:
        return False
    return True
