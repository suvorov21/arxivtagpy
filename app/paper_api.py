"""API for paper downloading."""

from time import sleep
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, time, date, timezone
import logging
from re import split
from typing import Tuple

from flask import current_app
from requests import get
import urllib3

from .model import Paper
from .utils import fix_xml


class ArxivOaiApi:
    """
    Arxiv.org harvester with  OAI_PMH v2.0.

    A better option comparing to API call.
    Much faster and no need for dummy search query.
    cons: download old papers where metadata was changed
    thus the "update" date was recent
    """
    BASE_URL = 'https://arxiv.org/'
    URL = 'http://export.arxiv.org/oai2?verb=ListRecords'
    DELAY = 3
    MAX_FAIL = 10

    BATCH_SIZE = 1000
    COMMIT_PERIOD = 1000

    DEF_PARAMS = {'metadataPrefix': 'arXivRaw'}

    OAI = "{http://www.openarchives.org/OAI/2.0/}"
    ARXIV = "{http://arxiv.org/OAI/arXivRaw/}"

    def __init__(self):
        """API initialisation."""
        self.params = ArxivOaiApi.DEF_PARAMS

    def set_set(self, set_var: str):
        """Set for papers."""
        self.params['set'] = set_var

    def set_from(self, from_var: str):
        """Set starting date."""
        self.params['from'] = from_var

    def set_until(self, until_var: str):
        """Set Until date."""
        self.params['until'] = until_var

    def get_ref_pdf(self, pid: str, version: str):
        """Format href for pdf doc."""
        return self.BASE_URL + '/pdf/' + pid + version + '.pdf'

    def get_ref_web(self, pid: str, version: str):
        """Format ref for webpage with summary."""
        return self.BASE_URL + '/abs/' + pid + version

    def download_papers(self, fail_attempts: int = 0, rest: int = -1):
        """Generator for paper downloading."""

        if fail_attempts > self.MAX_FAIL:
            logging.error('arXiv exceeds max allowed error limit')
            return

        logging.debug('Start harvesting')

        try:
            response = get(self.URL, self.params)
        except (urllib3.exceptions.MaxRetryError, urllib3.exceptions.NewConnectionError) as e:
            logging.warning('urllib3 exception')
            fail_attempts += 1
            sleep(self.DELAY)
            self.download_papers(fail_attempts=fail_attempts)
            yield from self.download_papers(rest=rest)

        logging.info('Ask arxiv with %r', response.url)

        if response.status_code != 200:
            fail_attempts += 1

            logging.warning('arXiv API response with %i',
                            response.status_code
                            )
            if 'Retry-After' in response.headers:
                delay = int(response.headers["Retry-After"])
                logging.warning('Sleeping for %i',
                                delay
                                )
                sleep(delay)

            sleep(self.DELAY)
            self.download_papers(fail_attempts=fail_attempts)
            yield from self.download_papers(rest=rest)

        lor = ET.fromstring(response.text).find(self.OAI + 'ListRecords')
        records = lor.findall(self.OAI + 'record')

        if len(records) != self.BATCH_SIZE and len(records) != rest:
            logging.warning('Download incomplete. Got %i from %i or %i',
                            len(records),
                            self.BATCH_SIZE,
                            rest
                            )

        updated = 'null'
        for record in records:
            info = record.find(self.OAI + 'metadata').find(self.ARXIV + 'arXivRaw')

            # WARNING is 'v?' tag always ordered?
            # assume yes, but who knows...
            versions = info.findall(self.ARXIV + 'version')
            created = versions[0].find(self.ARXIV + 'date').text
            created = created.split(', ')[1]
            created = datetime.strptime(created, "%d %b %Y %H:%M:%S GMT")

            updated = versions[-1].find(self.ARXIV + 'date').text
            updated = updated.split(', ')[1]
            updated = datetime.strptime(updated, "%d %b %Y %H:%M:%S GMT")

            # use only first doi
            doi = info.find(self.ARXIV+"doi")
            if doi is not None:
                doi = doi.text.split()[0]

            author = info.find(self.ARXIV + 'authors').text
            # explicitly for people who put affiliation in author list
            author = split(r', | \(.*?\),| and ', author)
            author[-1] = split(r' \(.*?\)(,|\s)', author[-1])[0]

            paper = Paper(paper_id=info.find(self.ARXIV + 'id').text,
                          title=fix_xml(info.find(self.ARXIV + 'title').text),
                          # TODO add helper function for author parse
                          author=author,
                          date_up=updated,
                          date_sub=created,
                          version=versions[-1].get('version'),
                          doi=doi,
                          abstract=fix_xml(info.find(self.ARXIV + 'abstract').text),
                          cats=info.find(self.ARXIV + 'categories').text.split(' '),
                          source=1
                          )

            yield paper

        # check if the next call is required
        token = lor.find(self.OAI + 'resumptionToken')
        if token is None or token.text is None:
            return

        rest = int(token.get('completeListSize')) % self.BATCH_SIZE

        logging.info('Going through resumption. Last date %r', updated)
        self.params = {'resumptionToken': token.text}

        sleep(self.DELAY)
        yield from self.download_papers(rest=rest)


def get_arxiv_sub_start(announce_date: date,
                        offset=0
                        ) -> datetime:
    """Get arxiv submission start time for a given announcement date."""
    deadline_time = current_app.config['ARXIV_DEADLINE_TIME']
    sub_date_begin = announce_date
    # papers announced on day N are submitted between day N-2 and N-1
    sub_date_begin -= timedelta(days=2 + offset)
    # over weekend cross
    # if the announcement date is on weekend
    # the situation is equivalent to Friday announcements
    # From Wednesday to Thursday
    if announce_date.weekday() > 4:
        sub_date_begin -= timedelta(days=sub_date_begin.weekday()-2)

    # on Monday papers from Thursday to Friday are announced
    if announce_date.weekday() == 0:
        sub_date_begin -= timedelta(days=2)

    # on Tuesday papers from Friday to Monday are announced
    if announce_date.weekday() == 1:
        sub_date_begin -= timedelta(days=2)

    # arxiv submission deadline is at 17:59
    sub_date_begin = datetime.combine(sub_date_begin,
                                      time(hour=deadline_time.hour - 1,
                                           minute=59,
                                           second=59
                                           )
                                      )

    return sub_date_begin


def get_arxiv_sub_end(announce_date: date) -> datetime:
    """Get arxiv submission end time for a given announcement date."""
    deadline_time = current_app.config['ARXIV_DEADLINE_TIME']
    sub_date_end = announce_date

    # papers announced on day N are submitted between day N-2 and N-1
    sub_date_end -= timedelta(days=1)

    # over weekend cross
    # if the announcement date is on weekend
    # the situation is equivalent to Friday announcements
    # From Wednesday to Thursday
    if announce_date.weekday() > 4:
        sub_date_end -= timedelta(days=sub_date_end.weekday()-3)
    # on Monday papers from Thursday to Friday are announced
    if announce_date.weekday() == 0:
        sub_date_end -= timedelta(days=2)

    # arxiv submission deadline is at 17:59
    sub_date_end = datetime.combine(sub_date_end,
                                    time(hour=deadline_time.hour-1,
                                         minute=59,
                                         second=59
                                         )
                                    )

    return sub_date_end


def get_arxiv_announce_date(paper_sub: datetime) -> datetime:
    """Get the announcement date for a given paper."""
    deadline_time = current_app.config['ARXIV_DEADLINE_TIME']
    announce_date = paper_sub
    announce_date = announce_date \
        + timedelta(days=1 if paper_sub.hour < deadline_time.hour else 2)
    if announce_date.weekday() > 4:
        announce_date = announce_date \
            + timedelta(days=7-announce_date.weekday())

    return announce_date


def get_annonce_date() -> datetime:
    """
    Compare the current time to the new paper announcement.

    If new papers are nor announced yet, switch announcement date to yesterday
    the announcement time is parametrized in UTC in .env file.
    """
    announce_date = datetime.now(timezone.utc)
    sub_update_time = current_app.config['ARXIV_UPDATE_TIME']
    sub_update_time = datetime.combine(announce_date.date(),
                                       time(hour=sub_update_time.hour,
                                            minute=sub_update_time.minute,
                                            tzinfo=timezone.utc
                                            )
                                       )
    if announce_date < sub_update_time:
        announce_date -= timedelta(days=1)

    return announce_date


def get_date_range(date_type: str,
                   announce_date: datetime,
                   **kwargs
                   ) -> Tuple[datetime, datetime, datetime]:
    """Return start and end for the submission range."""
    # tmp value stores the announced date of the paper
    new_date_tmp = announce_date
    # the real submission end period
    new_date = get_arxiv_sub_end(new_date_tmp.date())

    if date_type == 'today':
        old_date_tmp = announce_date
        logging.debug("Start for today %r", old_date_tmp)
        return old_date_tmp, announce_date, new_date

    if date_type == 'week':
        old_date_tmp = announce_date - \
                       timedelta(days=announce_date.weekday())
        logging.debug("Start for week %r", old_date_tmp)
        return old_date_tmp, announce_date, new_date

    if date_type == 'month':
        old_date_tmp = announce_date - \
                       timedelta(days=announce_date.day-1)
        if old_date_tmp.weekday() > 4:
            old_date_tmp += timedelta(days=7-old_date_tmp.weekday())

        logging.debug("Start for month %r", old_date_tmp)

        return old_date_tmp, announce_date, new_date

    if date_type == 'range':
        if kwargs.get('un') is None or kwargs.get('fr') is None:
            logging.error('Range date type but the arguments are empty')
            return announce_date, announce_date, announce_date

        new_date_tmp = datetime.strptime(kwargs['un'],
                                         '%d-%m-%Y'
                                         ).replace(tzinfo=timezone.utc)
        new_date = get_arxiv_sub_end(new_date_tmp.date())
        old_date_tmp = datetime.strptime(kwargs['fr'],
                                         '%d-%m-%Y'
                                         ).replace(tzinfo=timezone.utc)
        logging.debug("Start for range %r %r",
                      old_date_tmp,
                      new_date_tmp
                      )
        return old_date_tmp, new_date_tmp, new_date

    # the last uncovered request type
    # otherwise log an error
    if date_type not in {'unseen', 'last'}:
        logging.error('Unsupported date type %r', date_type)
    return announce_date, announce_date, announce_date
