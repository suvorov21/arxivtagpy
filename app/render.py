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

def render_papers(papers: Dict) -> Dict:
    """Convert papers dict to minimize info."""
    papers['papers'] = sorted(papers['papers'],
                              key=lambda t: t['tags'] if len(t['tags']) > 0 else [1000])

    # WARNING cross-fingered nobody will use 1000 tags
    # otherwise I'm in trouble

    for paper in papers['papers']:
        paper['date_sub'] = paper['date_sub'].strftime('%d %B %Y')

        if paper.get('date_up'):
            paper['date_up'] = paper['date_up'].strftime('%d %B %Y')

    return papers['papers']
