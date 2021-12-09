"""Some toolkit with utils."""

from os import linesep
import logging
from json import loads
from typing import List, Dict
from datetime import datetime, timedelta

import smtplib

from flask_mail import Message
from flask_login import current_user

from .import mail

from .model import PaperList, db, UpdateDate


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


def get_lists_for_user() -> List[Dict]:
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


def get_or_create_list(user_id, name) -> PaperList:
    """Find a list for a user in DB. If no, create one."""
    paper_list = PaperList.query.filter_by(user_id=user_id,
                                           name=name
                                           ).first()

    if not paper_list:
        paper_list = PaperList(name=name,
                               user_id=user_id,
                               not_seen=0
                               )
        db.session.add(paper_list)
        db.session.commit()

    return paper_list


def cast_args_to_dict(args) -> List[Dict]:
    """Cast requests args to dictionary."""
    prefs = []
    # TODO Fix key break with ampersand
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


def get_old_update_date() -> UpdateDate:
    """Check if the database record with latest update exists. If not create."""
    old_date_record = UpdateDate.query.first()
    if not old_date_record:
        old_date = month_start()
        old_date_record = UpdateDate(last_bookmark=old_date,
                                     last_email=old_date
                                     )
        db.session.add(old_date_record)
        db.session.commit()

    return old_date_record
