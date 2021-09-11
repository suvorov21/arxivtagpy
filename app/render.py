"""Render utils."""

from datetime import datetime
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
           '\\^e': '&ecirc;',
           '\\^E': '&Ecirc;',
           '\\"e': '&euml;',
           '\\"E': '&Euml;'
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
               last_visit.strftime('%d %b %Y')
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
        if old.date() == new.date():
            return 'for ' + datetime.strftime(old, '%A, %d %B')

        return 'from ' + \
               datetime.strftime(old, '%d %B') + ' until ' + \
               datetime.strftime(new, '%d %B')
    if date in ('last', 'unseen'):
        return ''

    return 'Papers'


def key_tag(paper):
    """Key for sorting with tags."""
    # Primary key is the 1st tag
    # secondary key is for date

    # to make the secondary key working in the right way
    # the sorting is reversed
    # for consistancy the tag index is inversed too

    # WARNING cross-fingered nobody will use 1000 tags
    # otherwise I'm in trouble
    return -paper['tags'][0] if len(paper['tags']) > 0 else -1000, \
        paper['date_up']


def key_date_up(paper):
    """Sorting with date."""
    return paper['date_up']


def render_papers(papers: dict, **kwargs):
    """Convert papers dict to minimize info."""
    if kwargs.get('sort'):
        reverse = True
        key = key_tag

        if kwargs['sort'] == 'date_up':
            key = key_date_up
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


def render_tags_front(tags: list) -> list:
    """Get rid of additional info about tags at front end."""
    tags_dict = [{'color': tag['color'],
                  'name': tag['name']
                  } for tag in tags]

    return tags_dict


def tag_name_and_rule(tags: list[Tag]) -> list:
    """Return only tag name and rule in JSON."""
    json = []
    for tag in tags:
        json.append({'name': tag.name,
                     'rule': tag.rule
                     })
    return json
