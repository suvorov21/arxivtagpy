"""Some toolkit with utils that are independent of the app."""

from os import linesep

from json import loads, JSONDecodeError
from typing import List, Dict
from datetime import datetime, timedelta

from flask import current_app, flash

from jwt import decode, encode, InvalidTokenError, ExpiredSignatureError


def fix_xml(xml: str) -> str:
    """
    Parse xml tag content.

    Remove line endings and double spaces.
    """
    return xml.replace(linesep, " ").replace("  ", " ")


def resolve_doi(doi: str) -> str:
    """Resolve doi string into link."""
    if not doi:
        return ''
    return 'https://www.doi.org/' + doi


def cast_args_to_dict(args) -> List[Dict]:
    """Cast requests args to dictionary."""
    prefs = []
    # WARNING Fix key break with ampersand
    for arg in args:
        prefs.append(arg)

    prefs = '&'.join(prefs)

    if prefs == '':
        return list()

    # convert to array of dict
    try:
        prefs = loads(prefs)
    except JSONDecodeError:
        return list()

    if isinstance(prefs, dict):
        prefs = [prefs]

    return prefs


def month_start() -> datetime:
    """Return the first day of the month."""
    today_date = datetime.now()
    # if month just stated --> take the previous one
    today_date -= timedelta(days=5)
    return today_date - timedelta(days=today_date.day)


class DecodeException(Exception):
    """Custom exception for token decode error."""


def encode_token(payload: Dict) -> str:
    """Helper for token creation."""
    return encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')


def decode_token(token: str, **kwargs) -> Dict:
    """Helper for token decode."""
    try:
        decoded = decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
    except ExpiredSignatureError:
        flash('ERROR! Link is expired, please try again.')
        raise DecodeException
    except InvalidTokenError:
        flash('ERROR! Invalid link, please try again.')
        raise DecodeException

    if 'keys' in kwargs:
        for key in kwargs.get('keys'):
            if key not in decoded:
                raise DecodeException

    return decoded


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
