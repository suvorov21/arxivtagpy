"""Render utils."""

from typing import Dict, List
from datetime import datetime
from .model import Tag

# dictionary for acccents
accents = {"\\'a": '&agrave;',
           "\\'A": '&Agrave;',
           "\\'e": '&eacute;',
           "\\'E": '&Eacute;',
           '\\"u': '&uuml;',
           '\\"U': '&Uuml;',
           "\\'i": '&iacute;',
           "\\'I": '&Iacute;',
           "\\`a": '&agrave;',
           "\\`A": '&Agrave;',
           "\\`e": '&egrave;',
           "\\`E": '&Egrave;',
           "\\'u": '&uacute;',
           "\\'U": '&Uacute;',
           "\\'c": '&cacute;',
           "\\'C": '&Cacute;',
           "\\`u": '&ugrave;',
           "\\`U": '&Ugrave;',
           '\\~n': '&ntilde;',
           '\\~N': '&Ntilde;',
           '\\c{c}': '&ccedil;',
           '\\"o': '&ouml;',
           '\\"O': '&Ouml;',
           "\\'o": '&oacute;',
           "\\'O": '&Oacute;',
           "\\`o": '&ograve;',
           "\\`O": '&Ograve;',
           "\\v{z}": '&zcaron;',
           "\\v{Z}": '&Zcaron;',
           "\\v{s}": '&scaron;',
           "\\v{S}": '&Scaron;'
           }

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
        reverse = False
        if  kwargs['sort'] == 'tag':
            # WARNING cross-fingered nobody will use 1000 tags
            # otherwise I'm in trouble
            key = lambda t: t['tags'] if len(t['tags']) > 0 else [1000]
        elif kwargs['sort'] == 'date_up':
            key = lambda t: t['date_up']
            reverse = True
        papers['papers'] = sorted(papers['papers'],
                                  key=key,
                                  reverse=reverse
                                  )

    for paper in papers['papers']:
        # cut author list and join to string
        if paper.get('author') and len(paper['author']) > 4:
            paper['author'] = paper['author'][:1]
            paper['author'].append('et al')
        paper['author'] = ', '.join(paper['author'])

        # fix accents in author list
        for key, value in accents.items():
            paper['author'] = paper['author'].replace(key, value)

        # render dates
        paper['date_sub'] = paper['date_sub'].strftime('%d %B %Y')

        if paper.get('date_up'):
            paper['date_up'] = paper['date_up'].strftime('%d %B %Y')

def render_tags_front(tags: Dict) -> Dict:
    """Get rid of additional info about tags at front end."""
    tags_dict = [{'color': tag['color'],
                  'name': tag['name']
                  } for tag in tags]

    return tags_dict

def tag_name_and_rule(tags: List[Tag]) -> List:
    """Return only tag name and rule in JSON."""
    json = []
    for tag in tags:
        json.append({'name': tag.name,
                     'rule': tag.rule
                     })
    return json
