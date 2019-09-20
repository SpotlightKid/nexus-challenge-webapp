# -*- coding: utf-8 -*-
"""Competition blueprint models."""

# Standard library modules
import datetime as dt

# Application specific modules
from nexus_challenge.database import Column, Model, SurrogatePK, db, reference_col, relationship


class CompetitionEntry(SurrogatePK, Model):
    """An entry submitted into the competition."""

    __tablename__ = 'competition_entries'
    title = Column(db.String(100), nullable=False)
    artist = Column(db.String(100), nullable=False)
    url = Column(db.String(255), nullable=False)
    description = Column(db.String(1000))
    production_details = Column(db.String(1000))

    is_published = db.Column(db.Boolean, nullable=False, default=False)
    is_approved = db.Column(db.Boolean, nullable=False, default=False)
    created_on = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    last_modified_on = Column(db.DateTime, nullable=False)
    published_on = Column(db.DateTime)

    user_id = reference_col('users', nullable=True)
    user = relationship('User', backref='competition_entries')

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<CompetitionEntry({artist} - {title})>'.format(artist=self.artist, title=self.title)


class Vote(SurrogatePK, Model):
    """A vote for an entry submitted into the competition."""

    __tablename__ = 'competition_votes'
    entry_id = reference_col('competition_entries', nullable=True)
    entry = relationship('CompetitionEntry', backref='votes')
    points = Column(db.Integer, nullable=False, default=0)
    created_on = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    user_id = reference_col('users', nullable=True)
    user = relationship('User', backref='votes')

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Vote(user: {user}, entry: "{artist} - {title}", points: {points})>'.format(
            user=self.user.username,
            artist=self.entry.artist,
            title=self.entry.title,
            points=self.points
        )
