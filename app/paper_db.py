"""
Interface for the paper table in the DB.

Paper downloader function update the paper DB
Query request to the DB.
"""

import logging
from datetime import datetime
from typing import List

from .interfaces.model import db, Paper, PaperCacheDay, PaperCacheWeeks
from .utils_app import get_old_update_date


def update_papers(api_list: List, **kwargs):
    """
    Update paper table.

    Get papers from all API with download_papers()
    and store in the DB.
    """
    for api in api_list:
        update_paper_per_api(api, **kwargs)

    db.session.commit()


def update_paper_per_api(api, **kwargs):
    """Update papers for a given API."""
    n_papers = kwargs.get('n_papers')
    last_paper_date = kwargs['last_paper_date']

    updated = 0
    downloaded = 0

    for paper in api.download_papers():
        # stoppers
        if n_papers and updated + downloaded > n_papers:
            break

        # too old paper. Skip
        if paper.date_up < last_paper_date:
            continue

        paper_prev = Paper.query.filter_by(paper_id=paper.paper_id).first()

        if paper_prev:
            if kwargs.get('do_update'):
                update_paper_record(paper_prev, paper)
                updated += 1
        else:
            db.session.add(paper)
            downloaded += 1

        if (updated + downloaded) % api.COMMIT_PERIOD == 0:
            logging.info('read %i papers', updated + downloaded)
            db.session.commit()

    logging.info('Paper update %s done: %i new; %i updated',
                 api.__class__.__name__,
                 downloaded,
                 updated
                 )


def update_paper_record(paper_prev: Paper, paper: Paper):
    """Update the paper record."""
    paper_prev.title = paper.title
    paper_prev.date_up = paper.date_up
    paper_prev.author = paper.author
    paper_prev.doi = paper.doi
    paper_prev.version = paper.version
    paper_prev.abstract = paper.abstract
    paper_prev.cats = paper.cats


def get_papers_from_db(cats: list,
                       old_date: datetime,
                       new_date: datetime
                       ) -> List[Paper]:
    """Make the DB request."""
    source = Paper
    old_date_record = get_old_update_date()
    if old_date_record.first_paper_day_cache and old_date >= old_date_record.first_paper_day_cache:
        source = PaperCacheDay
    elif old_date_record.first_paper_weeks_cache and old_date >= old_date_record.first_paper_weeks_cache:
        source = PaperCacheWeeks
    paper_query = source.query.filter(
        source.cats.overlap(cats),
        source.date_up > old_date,
        source.date_up < new_date,
    ).order_by(source.date_up.desc()).all()

    return paper_query
