from . import db
from flask_login import UserMixin

from sqlalchemy.dialects import postgresql as pg

class User(UserMixin, db.Model):
    """User table description."""
    __tablename__ = 'users'

    id = db.Column(db.Integer,
                   primary_key=True
                   )
    pasw = db.Column(db.String(),
                     nullable=False,
                     unique=False
                    )
    email = db.Column(db.String(),
                      nullable=False,
                      unique=True)
    created = db.Column(db.DateTime(),
                        nullable=True,
                        unique=False)

    login = db.Column(db.DateTime(),
                      nullable=True,
                      unique=False,
                      )
    last_paper = db.Column(db.DateTime(),
                           nullable=True,
                           unique=False,
                           )

    arxiv_cat = db.Column(db.ARRAY(db.String),
                          nullable=True,
                          unique=False
                          )
    tags = db.Column(db.String(),
                     nullable=True,
                     unique=False
                     )
    pref = db.Column(db.String(),
                     nullable=True,
                     unique=False
                     )

    lists = db.relationship('PaperList',
                             backref='user',
                             cascade='all,delete',
                             passive_deletes=True,
                             lazy=True
                             )

    def __repr__(self):
        """Print user."""
        return f'<id: {self.id} name: {self.name}>'

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
                                      db.ForeignKey('papers.id'),
                                      primary_key=True
                                      )
                            )

class Paper(db.Model):
    """Paper table description."""
    __tablename__ = 'papers'

    id = db.Column(db.Integer,
                   primary_key = True
                   )

    paper_id = db.Column(db.String(),
                         unique = True,
                         nullable=False
                         )

    title = db.Column(db.String(),
                     unique = False,
                     nullable=False
                     )

    author = db.Column(db.ARRAY(db.String),
                       unique=False,
                       nullable=False
                       )

    date_up = db.Column(db.DateTime(),
                        unique=False,
                        nullable=False
                        )

    date_sub = db.Column(db.DateTime(),
                         unique=False,
                         nullable=False
                         )

    abstract = db.Column(db.String(),
                         unique=False,
                         nullable=True
                         )

    ref_pdf = db.Column(db.String(),
                        unique=False,
                        nullable=True
                        )

    ref_web = db.Column(db.String(),
                        unique=False,
                        nullable=True
                        )

    ref_doi = db.Column(db.String(),
                        unique=False,
                        nullable=True
                        )

    cats = db.Column(pg.ARRAY(db.Text, dimensions=1),
                     unique=False,
                     nullable=True
                     )

    list_id = db.relationship('PaperList',
                              secondary=paper_associate,
                              lazy='subquery',
                              backref=db.backref('paper', lazy=True)
                              )

    def __repr__(self):
        """Print paper."""
        return f'<id: {self.id} title: {self.title}>'

class PaperList(db.Model):
    """Paper list table description."""
    __tablename__ = 'lists'
    id = db.Column(db.Integer,
                   primary_key = True
                   )

    name = db.Column(db.String(),
                     nullable=False,
                     unique=False
                     )

    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id',
                                      ondelete='CASCADE'
                                      ),
                        nullable=False
                        )

    papers = db.relationship('Paper',
                             secondary=paper_associate,
                             lazy='subquery',
                             backref=db.backref('paper_list', lazy=True)
                             )

    def __repr__(self):
        """Print paper."""
        return f'<id: {self.id} title: {self.name}>'
