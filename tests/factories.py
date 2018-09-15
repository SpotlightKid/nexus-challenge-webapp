# -*- coding: utf-8 -*-
"""Factories to help in tests."""

from factory import Sequence
from factory.alchemy import SQLAlchemyModelFactory

from fmchallengewebapp.database import db
from fmchallengewebapp.user.models import User


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
