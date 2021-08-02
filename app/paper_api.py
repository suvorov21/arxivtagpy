"""API for papr downloading."""

from time import sleep
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, time, date, timezone
import logging
from re import split

from flask import current_app
from requests import get

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

    DEF_PARAMS = {'metadataPrefix' : 'arXivRaw'}

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
        """Forrmat ref for webpage with summary."""
        return self.BASE_URL + '/abs/' + pid + version

    def download_papers(self):
        """Generator for paper downloading."""
        fail_attempts = 0
        rest = -1

        while True:
            logging.debug('Start harvesting')

            response = get(self.URL, self.params)
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

                if fail_attempts > self.MAX_FAIL:
                    logging.error('arXiv exceeds max allowed error limit')
                    return

                sleep(self.DELAY)
                continue

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
                # explicitly for peopple who put affillation in author list
                author = split(r', | \(.*?\),| and ', author)
                author[-1] = split(r' \(.*?\)(,| )', author[-1])[0]

                paper = Paper(paper_id=info.find(self.ARXIV + 'id').text,
                              title=fix_xml(info.find(self.ARXIV + 'title').text),
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

            print(token.get('completeListSize'))
            rest = int(token.get('completeListSize')) % self.BATCH_SIZE

            logging.info('Going through resumption. Last date %r', updated)
            self.params = {'resumptionToken': token.text}

            sleep(self.DELAY)

        return

def get_arxiv_sub_start(announce_date: date,
                        offset=0
                        ) -> datetime:
    """Get arxiv submission start time for a given announcment date."""
    sub_date_begin = announce_date
    # papers announced on day N are submitted between day N-2 and N-1
    sub_date_begin -= timedelta(days=2 + offset)
    # over weekend cross
    # if the announce date is on weekend
    # the situation is equivavlent to Friday announcments
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
                                     time(hour=17, minute=59, second=59)
                                     )

    return sub_date_begin

def get_arxiv_sub_end(announce_date: date) -> datetime:
    """Get arxiv submission end time for a given announcment date."""
    sub_date_end = announce_date

    # papers announced on day N are submitted between day N-2 and N-1
    sub_date_end -= timedelta(days=1)

    # over weekend cross
    # if the announce date is on weekend
    # the situation is equivavlent to Friday announcments
    # From Wednesday to Thursday
    if announce_date.weekday() > 4:
        sub_date_end -= timedelta(days=sub_date_end.weekday()-3)
    # on Monday papers from Thursday to Friday are announced
    if announce_date.weekday() == 0:
        sub_date_end -= timedelta(days=2)

    # arxiv submission deadline is at 17:59
    sub_date_end = datetime.combine(sub_date_end,
                                    time(hour=17, minute=59, second=59)
                                    )

    return sub_date_end

def get_axiv_announce_date(paper_sub: datetime) -> datetime:
    """Get the announce date for a given paper."""
    announce_date = paper_sub
    announce_date = announce_date \
        + timedelta(days=1 if paper_sub.hour < 18 else 2)
    if (announce_date.weekday() > 4):
        announce_date = announce_date \
            + timedelta(days=7-announce_date.weekday())

    return announce_date

def get_annonce_date() -> datetime:
    """
    Compare the current time to the new paper announcment.

    If new papers are nor announced yet, switch annoncment date to yesterday
    the announcment time is parametrized in UTC in .env file.
    """
    announce_date = datetime.now(timezone.utc)
    sub_update_time = current_app.config['UPDATE_TIME']
    sub_update_time = datetime.combine(announce_date.date(),
                                       time(hour=sub_update_time.hour,
                                            minute=sub_update_time.minute,
                                            tzinfo=timezone.utc
                                            )
                                        )
    if announce_date < sub_update_time:
        announce_date -= timedelta(days=1)

    return announce_date
