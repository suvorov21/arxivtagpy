"""Description of the inner app data structures."""

from datetime import datetime
from os import name
from typing import Tuple, Dict, List

from .model import Paper, Tag, PaperList
from ..utils import resolve_doi, accents
from ..paper_api import ArxivOaiApi

DATA_FORMAT = '%d %B'

class PaperInterface:
    """Stores the info about paper."""
    def __init__(self, db_id, paper_id, title, author, date_up, date_sub, version, doi, abstract, cats, source):
        self.id = db_id
        self.paper_id = paper_id
        self.title = title
        self.author = author
        self.date_up = date_up
        self.date_sub = date_sub
        self.version = version
        self.doi = doi
        self.abstract = abstract
        self.cats = cats
        self.source = source
        # values to be filled at processing
        self.tags = []
        self.nov = 0

    @classmethod
    def for_tests(cls, title, author, abstract):
        """Create a dummy paper."""
        return PaperInterface(1, '', title, author, None, None, '1', '', abstract, [], 1)

    def __getitem__(self, key) -> str:
        """Subscript is used at tag check."""
        if key == 'au':
            return ', '.join(self.author)
        elif key == 'ti':
            return self.title
        elif key == 'abs':
            return self.abstract
        elif key == 'cat':
            return ', '.join(self.cats)

        return ''

    def to_json(self) -> Dict:
        """Convert to JSON."""
        # cut author list and join to string
        if self.author and len(self.author) > 4:
            self.author = self.author[:1]
            self.author.append('et al')
        self.author = ', '.join(self.author)

        # fix accents in author list
        for key, value in accents.items():
            self.author = self.author.replace(key, value)

        return {'id': self.paper_id,
                'title': self.title,
                'author': self.author,
                'date_up': self.date_up.strftime('%d %B %Y'),
                'date_sub': self.date_sub.strftime('%d %B %Y'),
                'version': self.version,
                'doi': self.doi if self.doi else '',
                'abstract': self.abstract,
                'cats': self.cats,
                'tags': self.tags,
                'ref_web': ArxivOaiApi.get_ref_web(self.paper_id, self.version),
                'ref_pdf': ArxivOaiApi.get_ref_pdf(self.paper_id, self.version),
                'ref_doi': resolve_doi(self.doi)
                }

    @classmethod
    def from_paper(cls, paper_db: Paper):
        return PaperInterface(paper_db.id,
                              paper_db.paper_id,
                              paper_db.title,
                              paper_db.author,
                              paper_db.date_up,
                              paper_db.date_sub,
                              paper_db.version,
                              paper_db.doi,
                              paper_db.abstract,
                              paper_db.cats,
                              paper_db.source
                              )


class TagInterface:
    """Interface for the tag."""
    def __init__(self,
                 tag_id=-1,
                 order=-1,
                 name="",
                 rule="",
                 color="",
                 bookmark=False,
                 email=False,
                 public=False,
                 userss=False,
                 user_id=-1):
        self.id = tag_id
        self.order = order
        self.name = name
        self.rule = rule
        self.color = color
        self.bookmark = bookmark
        self.email = email
        self.public = public
        self.userss = userss
        self.user_id = user_id

    @classmethod
    def from_tag(cls, tag_db=Tag):
        return TagInterface(tag_db.id,
                            tag_db.order,
                            tag_db.name,
                            tag_db.rule,
                            tag_db.color,
                            tag_db.bookmark,
                            tag_db.email,
                            tag_db.public,
                            tag_db.userss,
                            tag_db.user_id
                            )

    @classmethod
    def from_name_and_rule(cls, tag_db: Tag):
        result = TagInterface()
        result.name = tag_db.name
        result.rule = tag_db.rule
        return result

    @classmethod
    def from_name_and_color(cls, tag_db: Tag):
        result = TagInterface()
        result.name = tag_db.name
        result.color = tag_db.color
        return result

    def to_front(self) -> Dict:
        return {'color': self.color,
                'name': self.name
                }

    def to_name_and_rule(self) -> Dict:
        return {'name': self.name,
                'rule': self.rule
                }

    def to_detailed_dict(self):
        return {'id': self.id,
                'name': self.name,
                'rule': self.rule,
                'color': self.color,
                'bookmark': self.bookmark,
                'email': self.email,
                'userss': self.userss,
                'public': self.public
                }


class PaperResponse:
    """Response with paper data, e.g. papers itself, counters."""
    def __init__(self, date=None):
        self.papers = []
        self.ncat = None
        self.nnov = None
        self.ntag = None
        self.last_date = date
        self.title = ''
        self.lists = []

    @staticmethod
    def key_tag(paper: PaperInterface) -> Tuple[int, datetime]:
        """Key for sorting with tags."""
        # Primary key is the 1st tag
        # secondary key is for date

        # to make the secondary key working in the right way
        # the sorting is reversed
        # for consistency the tag index is inverse too

        # WARNING cross-fingered nobody will use 1000 tags
        # otherwise I'm in trouble
        return -paper.tags[0] if len(paper.tags) > 0 else -1000, paper.date_up

    @staticmethod
    def key_date_up(paper: PaperInterface) -> datetime:
        """Sorting with date."""
        return paper.date_up

    @staticmethod
    def key_date_sub(paper: PaperInterface) -> datetime:
        """Sorting with date."""
        return paper.date_sub

    def sort_papers(self, key_type: str = 'tag', reverse: bool = True) -> None:
        """Sort the papers in response."""
        key_function = self.key_tag

        if key_type == 'date-up':
            key_function = self.key_date_up
        elif key_type == 'date-sub':
            key_function = self.key_date_sub

        self.papers = sorted(self.papers,
                             key=key_function,
                             reverse=reverse
                             )

    def render_papers(self) -> List[Dict]:
        """Render papers for the frontend."""
        return [paper.to_json() for paper in self.papers]

    def render_title_precise(self, date: str, old: datetime, new: datetime) -> None:
        """Render title based on the computed dates."""
        if date == 'today':
            self.title = datetime.strftime(new, '%A, %d %B')
            return
        if date in ('week', 'month'):
            self.title = datetime.strftime(old, DATA_FORMAT) + ' - ' + \
                         datetime.strftime(new, DATA_FORMAT)
            return
        if date == 'range':
            if old.date() == new.date():
                self.title = 'for ' + datetime.strftime(old, '%A, %d %B')
                return

            self.title = 'from ' + \
                         datetime.strftime(old, DATA_FORMAT) + ' until ' + \
                         datetime.strftime(new, DATA_FORMAT)
            return
        if date == 'last':
            self.title = ' on ' + datetime.strftime(old, DATA_FORMAT)
            return

        if date == 'unseen':
            self.title = ''
            return

        self.title = 'Papers'

    def to_dict(self) -> Dict:
        return {'papers': self.render_papers(),
                'ncat': self.ncat,
                'ntag': self.ntag,
                'nnov': self.nnov,
                'title': self.title,
                'lists': self.lists
                }


class PaperListInterface:
    """Interface for the paper lists."""
    def __init__(self,
                 list_id=-1,
                 order=-1,
                 name="",
                 user_id=-1,
                 not_seen=0):
        self.list_id = list_id
        self.order = order
        self.name = name
        self.user_id = user_id
        self.not_seen = not_seen

    @classmethod
    def from_id(cls, list_db: PaperList):
        result = PaperListInterface()
        result.id = list_db.id
        return result

    @classmethod
    def from_id_name(cls, list_db: PaperList):
        result = PaperListInterface()
        result.id = list_db.id
        result.name = list_db.name
        return result

    def to_dict(self):
        return {'name': self.name,
                'not_seen': self.not_seen,
                'id': self.list_id
                }

