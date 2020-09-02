from . import db
from flask_login import UserMixin

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
    arxiv_cat = db.Column(db.ARRAY(db.String),
                          nullable=True,
                          unique=False
                          )
    tags = db.Column(db.String(),
                     nullable=True,
                     unique=False
                     )

    def __repr__(self):
        return f'<id: {self.id} name: {self.name}>'
