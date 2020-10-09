from json import dumps
from urllib.parse import quote
from typing import List, Dict, Tuple

def render_title(date_type: int = 0) -> str:
    """Put the date type in the title text."""
    if date_type == 0:
        return 'Papers for today'
    if date_type == 1:
        return 'Papers for this week'
    if date_type == 2:
        return 'Papers for this month'
    if date_type == 3:
        return 'Papers since your last visit'
    return 'Papers'

def render_papers(papers: Dict) -> Dict:
    """Convert papers dict to minimize info"""

    # cross-fingered nobody will use 1000 tags
    # otherwise I'm in trouble
    papers['content'] = sorted(papers['content'],
                               key=lambda t: t['tags'] if len(t['tags'])>0 else [1000])

    for paper in papers['content']:
        if paper.get('author') and len(paper['author']) > 4:
            paper['author'] = paper['author'][:4]
            paper['author'].append('et al')

        # Put submit date only if updated
        if paper.get('date_sub') \
        and paper.get('date_sub') != paper.get('date_up'):
            paper['date_sub'] = paper['date_sub'].strftime('%d %B %Y')
        else:
            paper['date_sub'] = None

        if paper.get('date_up'):
            paper['date_up'] = paper['date_up'].strftime('%d %B %Y')

    return papers['content']
