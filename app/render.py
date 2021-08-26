"""Render utils."""

from typing import Dict, List
from datetime import datetime, timedelta
from .model import Tag

# dictionary for acccents
accents = {"\\'a": '&aacute;',
           "\\'A": '&Aacute;',
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
           "\\v{S}": '&Scaron;',
           "\v{c}": "&ccaron;",
           "\v{C}": "&Ccaron;",
           "{\\aa}": '&aring;',
           "{\\AA}": '&aring;',
           '\\"a': '&auml;',
           '\\"A': '&Auml;',
           '\\v{c}': '&cdot;',
           '\\v{C}': '&Cdot;',
           }

def render_title(date_type: str, last_visit: datetime = 0) -> str:
    """Put the date type in the title text."""
    if date_type == 'today':
        return 'Papers for today'
    elif date_type == 'week':
        return 'Papers for this week'
    elif date_type == 'month':
        return 'Papers for this month'
    elif date_type == 'last':
        return 'Papers since your last visit on ' + \
                (last_visit).strftime('%d %b %Y')
    elif date_type == 'unseen':
        return 'Unseen papers during the past week'

    return 'Papers'

def render_title_precise(date: str, old: datetime, new: datetime) -> str:
    """Render title based on the computed dates."""
    if date == 'today':
        return datetime.strftime(new, '%A, %d %B')
    if date in ('week', 'month'):
        return datetime.strftime(old, '%d %B') + ' - ' + \
               datetime.strftime(new, '%d %B')
    if date == 'range':
        if (old.date() == new.date()):
            return 'for ' + datetime.strftime(old, '%A, %d %B')
        else:
            return 'from '  + \
                   datetime.strftime(old, '%d %B') + ' until ' + \
                   datetime.strftime(new, '%d %B')
    if date == 'last' || date == 'unseen':
        return ''

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
