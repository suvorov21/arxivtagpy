"""
Papers parsers utils.

Tag processor checks if a given paper is suitable with the tag
"""

from re import search, compile, IGNORECASE, error
from datetime import datetime, timedelta
import logging

from typing import List, Tuple
from sentry_sdk import start_transaction

from .interfaces.data_structures import PaperInterface, PaperResponse, TagInterface
from .paper_api import get_date_range, get_arxiv_sub_start
from .paper_db import get_papers_from_db


def process_nov(paper: PaperInterface, nov_counters: list, cats: list, last_date: datetime):
    """Check novelty of the papers. Update counters."""
    # 1.a check if cross-ref
    if paper.cats[0] not in cats:
        nov_counters[1] += 1
        paper.nov += 2

    # 1.b count updated papers
    if paper.date_sub < last_date:
        paper.nov += 4
        nov_counters[2] += 1

    if paper.nov == 0:
        paper.nov = 1
        nov_counters[0] += 1


def process_tags(paper: PaperInterface,
                 tags: List[TagInterface],
                 tag_counter):
    """Apply tags for a given paper and increment a counter."""
    for num, tag in enumerate(tags):
        if tag_suitable(paper, tag.rule):
            paper.tags.append(num)
            tag_counter[num] += 1


def process_papers(response: PaperResponse,
                   tags: List[TagInterface],
                   cats: List,
                   do_nov: bool,
                   do_tag: bool
                   ) -> None:
    """
    Response processing. Count papers per category, per novelty, per tag.

    Process:
    1. novelty. use 'bit' map
        0 - undef 1 - new, 2 - cross, 4 - up
        a. cross-ref
        b. updated
    2. categories
    3. process tags
    """
    response.nnov = [0] * 3
    response.ncat = [0] * len(cats)
    response.ntag = [0] * len(tags)
    with start_transaction(op="paper_processing", name='papers'):
        for paper in response.papers:
            if do_nov:
                # count paper per category
                for cat in paper.cats:
                    if cat in cats:
                        response.ncat[cats.index(cat)] += 1
                process_nov(paper, response.nnov, cats, response.last_date)

            # 2.
            if do_tag:
                process_tags(paper, tags, response.ntag)


def find_or_and(rule: str) -> Tuple[List[int], List[int]]:
    """Utils function that finds positions of & and | outside {} and ()."""
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

    return or_pos, and_pos


def tag_suitable(paper: PaperInterface, rule: str) -> bool:
    """
    Checking rule for the given paper.

    The function is called recursively for checking different parts of the rule.
    1. Find logic AND / OR outside curly and round brackets
    2. If no - parse rules inside curly brackets
    3. OR: and process rule parts one by one separated by |
    return True at first true condition
    return False if no matches
    4. AND: process rule parts separated by &
    return False at first false match
    return True if no false matches

    :param      paper:       The paper
    :type       paper:       PaperInterface
    :param      rule:        The rule
    :type       rule:        str

    :returns:   if the paper suits the tag
    :rtype:     bool
    """
    logging.debug('Start tag parse with rule %r', rule)
    # remove parentheses if the whole rule is inside
    if rule[0] == '(' and rule[-1] == ')':
        rule = rule[1:-1]

    or_pos, and_pos = find_or_and(rule)

    # if no AND/OR found outside brackets process a rule inside curly brackets
    if len(and_pos) == 0 + len(or_pos) == 0:
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
    for num, pos in enumerate(and_pos[:-1]):
        if not tag_suitable(paper, rule[pos+1:and_pos[num+1]]):
            return False

    # if logic AND is inside the rule but False was not found
    return True


def parse_simple_rule(paper: PaperInterface, condition: str) -> bool:
    """Parse simple rules as ti/au/abs."""
    prefix_re = search(r'^(ti|abs|au|cat){(.*?)}', condition)
    if not prefix_re:
        return False

    prefix = prefix_re.group(1)
    condition = prefix_re.group(2)

    logging.debug('Initial simple rule %r', condition)

    search_target = paper[prefix]
    if not search_target:
        logging.error('Prefix is unknown %r', prefix)
    # in case of
    # 1. author
    # 2. Paper category
    #  the target is a list
    # join the list into string
    if isinstance(search_target, list):
        search_target = ', '.join(search_target)

    # cast logic AND to proper REGEX
    if '&' in condition:
        # split the condition with logic OR to cast the parts individually
        split_wit_or = condition.split('|')
        new_rule = []
        for or_subpart in split_wit_or:
            if '&' in or_subpart:
                # use non-consuming as logic AND
                cond_list = or_subpart.split('&')
                new_rule.append('(?=.*')
                new_rule[-1] += ')(?=.*'.join(cond_list)
                new_rule[-1] += ')'
            else:
                new_rule.append(or_subpart)

        # merge rule back together
        condition = '|'.join(new_rule)

    # inversion of the rule
    inversion = False
    if '!' in condition:
        condition = condition.replace('!', '')
        inversion = True

    logging.debug('Processing parse_simple_rule %r %r', prefix, condition)

    try:
        re_cond = compile(condition,
                          flags=IGNORECASE
                          )
    except error:
        logging.error('Error in RegExp: %r', condition)
        return False

    found = re_cond.search(search_target) is not None

    if found != inversion:
        logging.debug('Simple rule OK for %r', search_target)
        return True
    return False


def get_papers(cats: List[str],
               old_date: datetime,
               new_date: datetime
               ) -> List[PaperInterface]:
    """Get list of papers from DB."""
    paper_query = get_papers_from_db(cats, old_date, new_date)
    return [PaperInterface.from_paper(paper) for paper in paper_query]


def get_unseen_papers(cats: List[str],
                      recent_visit: int,
                      recent_range: int,
                      announce_date: datetime
                      ) -> List[PaperInterface]:
    """Get unseen papers from DB."""
    result = []
    for i in range(recent_range - 1):
        if not 2**i & recent_visit:
            if (announce_date - timedelta(days=i)).weekday() > 4:
                # no announcements on weekends
                continue
            old_date_tmp, new_date_tmp, new_date = get_date_range(
                                'today',
                                announce_date - timedelta(days=i)
                                )

            old_date = get_arxiv_sub_start(old_date_tmp.date())
            result.extend(get_papers(cats, old_date, new_date))
    return result
