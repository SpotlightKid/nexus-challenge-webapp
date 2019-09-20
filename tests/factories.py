# -*- coding: utf-8 -*-
"""Factories to help in tests."""

# Third-party modules
from factory import Sequence
from factory.alchemy import SQLAlchemyModelFactory

# Application specific modules
from nexus_challenge.database import db
from nexus_challenge.user.models import User


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory."""

    class Meta:
        """Factory configuration."""

        abstract = True
        sqlalchemy_session = db.session


class UserFactory(BaseFactory):
    """User factory."""

    username = Sequence(lambda n: 'user{0}'.format(n))
    email = Sequence(lambda n: 'user{0}@example.com'.format(n))
    is_active = True
    is_confirmed = True

    class Meta:
        """Factory configuration."""

        model = User
