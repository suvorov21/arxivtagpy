"""Render utils."""

# dictionary for accents
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
           '\\"E': '&Euml;',
           '\\~A': '&Atilde;',
           '\\~a': '&atilde;'
           }


def render_title(date_type: str) -> str:
    """Put the date type in the title text."""
    if date_type == 'today':
        return 'Papers for today'
    if date_type == 'week':
        return 'Papers for this week'
    if date_type == 'month':
        return 'Papers for this month'
    if date_type == 'last':
        return 'Papers since your last visit'
    if date_type == 'unseen':
        return 'Unseen papers during the past week'

    return 'Papers'


def render_tags_front(tags: list) -> list:
    """Get rid of additional info about tags at front end."""
    tags_dict = [{'color': tag['color'],
                  'name': tag['name']
                  } for tag in tags]

    return tags_dict


def tag_name_and_rule(tags: list) -> list:
    """Return only tag name and rule in JSON."""
    json = []
    for tag in tags:
        json.append({'name': tag.name,
                     'rule': tag.rule
                     })
    return json
