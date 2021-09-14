"""Some toolkit with utils."""

from os import linesep
import logging
from json import loads

import smtplib

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
    paper_lists = PaperList.query.filter_by(user_id=current_user.id
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
              'not_seen': paper_list.not_seen,
              'id': paper_list.id
              } for paper_list in paper_lists]

    return lists


def cast_args_to_dict(args) -> list:
    """Cast requests args to dictionary."""
    prefs = []
    # FIXME Fix key break with ampersand
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
