# -*- coding: utf-8 -*-
"""User blueprint models."""

import datetime as dt

from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property

from fmchallengewebapp.database import Column, Model, SurrogatePK, db, reference_col, relationship
from fmchallengewebapp.extensions import bcrypt


class Role(SurrogatePK, Model):
    """A role for a user."""

    __tablename__ = 'roles'
    name = Column(db.String(80), unique=True, nullable=False)
    user_id = reference_col('users', nullable=True)
    user = relationship('User', backref='roles')

    def __init__(self, name, **kwargs):
        """Create instance."""
        db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Role({name})>'.format(name=self.name)


class User(SurrogatePK, Model, UserMixin):
    """A user of the app."""

    __tablename__ = 'users'
    username = Column(db.String(80), unique=True, nullable=False)
    email = Column(db.String(80), unique=True, nullable=False)
    hashed_password = Column(db.Binary(128), nullable=True)
    first_name = Column(db.String(30), nullable=True)
    last_name = Column(db.String(30), nullable=True)
    is_active = Column(db.Boolean(), default=False)
    is_admin = Column(db.Boolean(), default=False)
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)
    created_on = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    password_reset_token = db.Column(db.String, nullable=True)

    @hybrid_property
    def password(self):
        """Get password."""
        return self.hashed_password

    @password.setter
    def password(self, value):
        """Set password."""
        self.hashed_password = bcrypt.generate_password_hash(value)

    def check_password(self, value):
        """Check password."""
        return bcrypt.check_password_hash(self.password, value)

    @property
    def full_name(self):
        """Full user name."""
        return '{0} {1}'.format(self.first_name, self.last_name)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<User({username!r})>'.format(username=self.username)
