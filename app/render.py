"""Render utils."""

from typing import Dict
from datetime import datetime

def render_title(date_type: int = 0, last_visit: datetime = 0) -> str:
    """Put the date type in the title text."""
    if date_type == 0:
        return 'Papers for today'
    if date_type == 1:
        return 'Papers for this week'
    if date_type == 2:
        return 'Papers for this month'
    if date_type == 3:
        return 'Papers since your last visit on ' + last_visit.strftime('%d %b %Y')
    return 'Papers'

def render_papers(papers: Dict, **kwargs) -> Dict:
    """Convert papers dict to minimize info."""
    if kwargs.get('sort'):
        if  kwargs['sort'] == 'tag':
            # WARNING cross-fingered nobody will use 1000 tags
            # otherwise I'm in trouble
            key = lambda t: t['tags'] if len(t['tags']) > 0 else [1000]
        elif kwargs['sort'] == 'date_up':
            key = lambda t: t['date_up']
        papers['papers'] = sorted(papers['papers'],
                                  key=key)

    for paper in papers['papers']:
        paper['date_sub'] = paper['date_sub'].strftime('%d %B %Y')

        if paper.get('date_up'):
            paper['date_up'] = paper['date_up'].strftime('%d %B %Y')

def render_tags_front(tags: Dict) -> Dict:
    """Get rid of additional info about tags at front end."""
    tags_dict = [{'color': tag['color'],
                  'name': tag['name']
                  } for tag in tags]

    return tags_dict
