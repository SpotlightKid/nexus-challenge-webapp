# -*- coding: utf-8 -*-
"""Model unit tests."""

# Standard library modules
import datetime as dt

# Third-party modules
import pytest

# Application specific modules
from nexus_challenge.user.models import Role, User

from .factories import UserFactory


@pytest.mark.usefixtures('db')
class TestUser:
    """User tests."""

    def test_get_by_id(self):
        """Get user by ID."""
        user = User.create(username='foo', email='foo@bar.com')

        retrieved = User.get_by_id(user.id)
        assert retrieved == user

    def test_created_on_defaults_to_datetime(self):
        """Test creation date."""
        user = User.create(username='foo', email='foo@bar.com')
        assert bool(user.created_on)
        assert isinstance(user.created_on, dt.datetime)

    def test_password_is_nullable(self):
        """Test null password."""
        user = User.create(username='foo', email='foo@bar.com')
        assert user.password is None

    def test_factory(self, db):
        """Test user factory."""
        user = UserFactory(password='myprecious')
        db.session.commit()
        assert bool(user.username)
        assert bool(user.email)
        assert bool(user.created_on)
        assert user.is_admin is False
        assert user.is_active is True
        assert user.check_password('myprecious')

    def test_check_password(self):
        """Check password."""
        user = User.create(username='foo', email='foo@bar.com',
                           password='foobarbaz123')
        assert user.check_password('foobarbaz123') is True
        assert user.check_password('barfoobaz') is False

    def test_full_name(self):
        """User full name."""
        user = UserFactory(first_name='Foo', last_name='Bar')
        assert user.full_name == 'Foo Bar'

    def test_roles(self):
        """Add a role to a user."""
        role = Role.create(name='admin')
        user = UserFactory()
        user.roles.append(role)
        user.save()
        assert role in user.roles
