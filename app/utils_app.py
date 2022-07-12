"""Utils pack that inherits tools from the app e.g. DB."""

import logging
import smtplib
from typing import List, Dict

from flask_mail import Message
from flask_login import current_user

from . import mail

from .interfaces.model import PaperList, db, UpdateDate
from .utils import month_start


def mail_catch(msg: Message) -> bool:
    """Catch email exceptions."""
    try:
        mail.send(msg)
    except smtplib.SMTPException:
        logging.error('Error sending email')
        return False

    return True


def query_lists_for_user(list_id: int) -> List[PaperList]:
    """Perform a query to DB to get list PaperLists w/o papers."""
    return db.session.query(PaperList).with_entities(PaperList.name,
                                                     PaperList.not_seen,
                                                     PaperList.id
                                                     ).filter(
        PaperList.user_id == list_id
    ).order_by(PaperList.order).all()


def get_lists_for_user() -> List[Dict]:
    """Get all paper lists for a given user."""
    paper_lists = query_lists_for_user(current_user.id)

    # if no, create the default list
    if len(paper_lists) == 0:
        from .auth import new_default_list
        new_default_list(current_user.id)
        paper_lists = query_lists_for_user(current_user.id)
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


def get_old_update_date() -> UpdateDate:
    """Check if the database record with the latest update exists. If not create."""
    old_date_record = UpdateDate.query.first()
    if not old_date_record:
        old_date = month_start()
        old_date_record = UpdateDate(last_bookmark=old_date,
                                     last_email=old_date,
                                     last_paper=old_date
                                     )
        db.session.add(old_date_record)
        db.session.commit()

    return old_date_record


def update_seen_papers(it_start, it_end):
    """Update "seen" papers."""
    for i in range(it_start, it_end + 1):
        # prevent underflow by 1
        i = max(i, 0)
        current_user.recent_visit = current_user.recent_visit | 2 ** i
