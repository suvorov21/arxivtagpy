"""API for papr downloading."""

from time import sleep
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, time
import logging
from re import split

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

    def set_from(self, from_var):
        """Set starting date."""
        self.params['from'] = from_var

    def get_ref_pdf(self, pid, version):
        """Format href for pdf doc."""
        return self.BASE_URL + '/pdf/' + pid + version + '.pdf'

    def get_ref_web(self, pid, version):
        """Forrmat ref for webpage with summary."""
        return self.BASE_URL + '/abs/' + pid + version

    def download_papers(self):
        """Generator for paper downloading."""
        fail_attempts = 0

        while True:
            logging.debug('Start harvesting')

            response = get(self.URL, self.params)
            logging.debug(response.url)

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

            if len(records) != self.BATCH_SIZE:
                logging.warning('Download may be incomplete. Got %i from %i',
                                len(records),
                                self.BATCH_SIZE
                                )

            for record in records:
                info = record.find(self.OAI + 'metadata').find(self.ARXIV + 'arXivRaw')

                # WARNING is 'v?' tag always ordered?
                # assum yes, but who knows...
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
            token = lor.find(self.OAI+"resumptionToken")
            if token is None or token.text is None:
                return

            logging.info('Going through resumption')
            self.params = {'resumptionToken': token.text}

            sleep(self.DELAY)

        return

def get_arxiv_last_date(today_date: datetime,
                        old_date: datetime,
                        date_type: int
                        ) -> datetime:
    """
    Get the data of the previous sumission deadline.

    The method helps to get "today's" submissions. As the submission date
    is actually "yesterday".
    arXiv has submission deadline at 18:00. So that the papers submitted
    before the deadline are published the next day, the papers who come
    after deadline are submitted in two days.
    """
    if date_type == 0:
        # look at the results of current date
        # last_submission_day - 1 day at 18:00Z
        old_date = today_date - timedelta(days=1)
    elif date_type == 1:
        # if last paper is published on Friday
        # "this week" starts from next Monday
        if today_date.weekday() == 4:
            old_date = today_date - timedelta(days=1)
        else:
            old_date = today_date - timedelta(days=today_date.weekday()+4)
    elif date_type == 2:
        old_date = today_date - timedelta(days=today_date.day)

    # over weekend cross
    if old_date.weekday() > 4 and date_type != 4:
        old_date = old_date - timedelta(days=old_date.weekday()-4)

    # papers are submitted by 18:00Z
    if date_type < 3:
        old_date = old_date.replace(hour=17, minute=59, second=59)
    else:
        old_date = datetime.combine(old_date,
                                    time(hour=17, minute=59, second=59))

    return old_date