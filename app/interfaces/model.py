"""Database model."""

from flask_login import UserMixin

from sqlalchemy.dialects import postgresql as pg

from app import db


class User(UserMixin, db.Model):
    """User table description."""
    __tablename__ = 'users'

    id = db.Column(db.Integer,
                   primary_key=True
                   )
    pasw = db.Column(db.String())
    orcid = db.Column(db.String(),
                      unique=True
                      )
    email = db.Column(db.String(),
                      unique=True
                      )
    verified_email = db.Column(db.Boolean,
                               nullable=False,
                               default=False
                               )
    created = db.Column(db.DateTime(),
                        nullable=False
                        )

    login = db.Column(db.DateTime(),
                      nullable=False,
                      )
    last_paper = db.Column(db.DateTime(),
                           nullable=True
                           )

    arxiv_cat = db.Column(pg.ARRAY(db.Text, dimensions=1),
                          nullable=True,
                          )
    tags = db.relationship('Tag',
                           backref='user',
                           cascade='all,delete',
                           passive_deletes=True,
                           lazy=True
                           )
    pref = db.Column(db.String(),
                     nullable=False,
                     )

    # bit mask that shows recent viewed days
    # 0 - no visits in 7 days
    # 1 - yesterday
    # 2 - 2 days ago, so on
    recent_visit = db.Column(db.Integer,
                             default=0
                             )

    lists = db.relationship('PaperList',
                            backref='user',
                            cascade='all,delete',
                            passive_deletes=True,
                            lazy=True
                            )

    def __repr__(self):
        """Print user."""
        return f'<User id: {self.id} name: {self.email}>'


class Tag(db.Model):
    """Table for storing user defined tags."""
    __tablename__ = 'tags'
    id = db.Column(db.Integer,
                   primary_key=True,
                   )

    order = db.Column(db.Integer,
                      nullable=False,
                      default=0
                      )

    name = db.Column(db.String(),
                     nullable=False
                     )

    rule = db.Column(db.String(),
                     nullable=False
                     )

    color = db.Column(db.String(),
                      nullable=False
                      )

    bookmark = db.Column(db.Boolean,
                         nullable=True,
                         default=False
                         )

    email = db.Column(db.Boolean,
                      nullable=True,
                      default=False
                      )

    public = db.Column(db.Boolean,
                       nullable=True,
                       default=False
                       )

    userss = db.Column(db.Boolean,
                       nullable=False,
                       default=True
                       )

    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id',
                                      ondelete='CASCADE'
                                      ),
                        nullable=False,
                        )

    def __repr__(self):
        """Print Tag."""
        return f'<Tag id: {self.id} name: {self.name}>'


class UpdateDate(db.Model):
    """
    Table to store update dates.

    Store dates of the last updates e.g. lst bookmarked
    or last email paper.
    """
    id = db.Column(db.Integer,
                   primary_key=True
                   )
    last_bookmark = db.Column(db.DateTime(),
                              nullable=True
                              )

    last_email = db.Column(db.DateTime(),
                           nullable=True
                           )
    last_paper = db.Column(db.DateTime(),
                           nullable=True
                           )
    first_paper_day_cache = db.Column(db.DateTime(),
                                      nullable=True
                                      )
    first_paper_weeks_cache = db.Column(db.DateTime(),
                                        nullable=True
                                        )


# helper table to deal with many-to-many relations
# lists --> papers
# return papers by paperlist Paper.query.with_parent(some_list)
paper_associate = db.Table('paper_associate',
                           db.Column('list_ref_id',
                                     db.Integer,
                                     db.ForeignKey('lists.id',
                                                   ondelete='CASCADE'
                                                   ),
                                     primary_key=True
                                     ),
                           db.Column('paper_ref_id',
                                     db.Integer,
                                     db.ForeignKey('papers.id',
                                                   ondelete='CASCADE'
                                                   ),
                                     primary_key=True
                                     )
                           )


class PaperModel(object):
    """Paper table description."""
    id = db.Column(db.Integer,
                   primary_key=True
                   )

    paper_id = db.Column(db.String(),
                         unique=True,
                         nullable=False
                         )

    title = db.Column(db.String(),
                      nullable=False
                      )

    author = db.Column(pg.ARRAY(db.Text, dimensions=1),
                       nullable=False
                       )

    date_up = db.Column(db.DateTime(),
                        nullable=False
                        )

    date_sub = db.Column(db.DateTime(),
                         nullable=False
                         )

    version = db.Column(db.String(),
                        nullable=False
                        )

    doi = db.Column(db.String(),
                    nullable=True,
                    )

    abstract = db.Column(db.String(),
                         nullable=True
                         )

    cats = db.Column(pg.ARRAY(db.Text, dimensions=1),
                     nullable=True
                     )

    # integer source numeration is cheaper than additional table
    # Actually, no need of additional table so far
    # by convention:
    # 1 := arXiv
    source = db.Column(db.Integer,
                       nullable=False
                       )

    def __repr__(self):
        """Print paper."""
        return f'<Paper id: {self.id} title: {self.title}>'


class Paper(PaperModel, db.Model):
    """The actual paper table."""
    __tablename__ = 'papers'


class PaperCacheDay(PaperModel, db.Model):
    """Table for paper caching for a day."""
    __tablename__ = 'papers_cache_day'


class PaperCacheWeeks(PaperModel, db.Model):
    """Table for paper caching for 14 days (2 weeks)."""
    __tablename__ = 'papers_cache_weeks'


class PaperList(db.Model):
    """Paper list table description."""
    __tablename__ = 'lists'
    id = db.Column(db.Integer,
                   primary_key=True
                   )

    order = db.Column(db.Integer,
                      nullable=False,
                      default=0
                      )

    name = db.Column(db.String(),
                     nullable=False,
                     )

    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id',
                                      ondelete='CASCADE'
                                      ),
                        nullable=False
                        )

    not_seen = db.Column(db.Integer,
                         nullable=True,
                         default=0
                         )

    papers = db.relationship('Paper',
                             secondary=paper_associate,
                             lazy='subquery',
                             backref=db.backref('paper_list', lazy=True)
                             )

    def __repr__(self):
        """Print paper list."""
        return f'<PaperList id: {self.id} title: {self.name}>'
