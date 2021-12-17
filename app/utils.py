"""Some toolkit with utils that are independent of the app."""

from os import linesep

from json import loads
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
    prefs = loads(prefs)

    if isinstance(prefs, dict):
        prefs = [prefs]

    return prefs


def month_start() -> datetime:
    """Return the first day of the month."""
    today_date = datetime.now()
    # if month just stated --> take the previous one
    if today_date.day < 3:
        today_date -= timedelta(days=4)
    return today_date - timedelta(days=today_date.day)


class DecodeException(Exception):
    """Custom exception for token decode error."""
    pass


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
