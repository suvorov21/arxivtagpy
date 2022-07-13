"""Description of the inner app data structures."""

from datetime import datetime
from typing import Tuple, Dict, List

from .model import Paper, Tag
from ..utils import resolve_doi, accents
from ..paper_api import ArxivOaiApi


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
                'ref_pdf': ArxivOaiApi.get_ref_web(self.paper_id, self.version),
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
    def __init__(self, tag_id, order, name, rule, color, bookmark, email, public, userss, user_id):
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

    def sort_papers(self, key_type='tag') -> None:
        """Sort the papers in response."""
        reverse = True
        key_function = self.key_tag

        if key_type == 'date_up':
            key_function = self.key_date_up

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
            self.title = datetime.strftime(old, '%d %B') + ' - ' + \
                         datetime.strftime(new, '%d %B')
            return
        if date == 'range':
            if old.date() == new.date():
                self.title = 'for ' + datetime.strftime(old, '%A, %d %B')
                return

            self.title = 'from ' + \
                         datetime.strftime(old, '%d %B') + ' until ' + \
                         datetime.strftime(new, '%d %B')
            return
        if date == 'last':
            self.title = ' on ' + datetime.strftime(old, '%d %B')
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
