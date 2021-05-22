"""Some toolkit with utils."""

from os import linesep
import logging

import smtplib

from flask import url_for
from flask_mail import Message

from .import mail

def fix_xml(xml: str) -> str:
    """
    Parse xml tag content.

    Remove line endings and double spaces.
    """
    return xml.replace(linesep, " ").replace("  ", " ")

def url(adress: str, **kwargs) -> str:
    """
    Fix the url removing the wsgi name.

    Seems to be host-specific issue.
    """
    tmp = url_for(adress, **kwargs)
    tmp = tmp.replace('/flask.wsgi/', '/')
    return tmp

def mail_catch(msg: Message) -> bool:
    """Catch email exceptions."""
    try:
        mail.send(msg)
    except smtplib.SMTPException:
        logging.error('Error sending email')
        return False

    return True
