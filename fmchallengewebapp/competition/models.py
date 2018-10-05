# -*- coding: utf-8 -*-
"""Competition blueprint models."""

import datetime as dt

from sqlalchemy.ext.hybrid import hybrid_property

from fmchallengewebapp.database import Column, Model, SurrogatePK, db, reference_col, relationship


class CompetitionEntry(SurrogatePK, Model):
    """An entyr submitted into the competition."""

    __tablename__ = 'competition_entries'
    title = Column(db.String(80), unique=True, nullable=False)
    artist = Column(db.String(80), nullable=False)
    url = Column(db.String(80), nullable=False)
    description = Column(db.String(500))
    production_details = Column(db.String(500))

    is_published = db.Column(db.Boolean, nullable=False, default=False)
    is_approved = db.Column(db.Boolean, nullable=False, default=False)
    created_on = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    published_on = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    user_id = reference_col('users', nullable=True)
    user = relationship('User', backref='competition_entries')

    def __init__(self, name, **kwargs):
        """Create instance."""
        db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Role({name})>'.format(name=self.name)

# ~    @hybrid_property
# ~    def password(self):
# ~        """Get password."""
# ~        return self.hashed_password

# ~    @password.setter
# ~    def password(self, value):
# ~        """Set password."""
# ~        self.hashed_password = bcrypt.generate_password_hash(value)

# ~    def check_password(self, value):
# ~        """Check password."""
# ~        return bcrypt.check_password_hash(self.password, value)
