"""Some toolkit with utils."""

from os import linesep
import logging

import smtplib

from flask import url_for
from flask_mail import Message
from flask_login import current_user

from .import mail

from .model import PaperList

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

def get_lists_for_user() -> list:
    """Get all paper lists for a given user."""
    # get all lists for the menu (ordered)
    paper_lists = PaperList.query.filter_by(user_id=current_user.id \
                                            ).order_by(PaperList.order).all()
    # if no, create the default list
    if len(paper_lists) == 0:
        from .auth import new_default_list
        new_default_list(current_user.id)
        paper_lists = PaperList.query.filter_by(user_id=current_user.id).all()
        logging.error('Default list was not created for user %r',
                      current_user.email
                      )

    lists = [{'name': paper_list.name,
              'not_seen': paper_list.not_seen
              } for paper_list in paper_lists]

    return lists
