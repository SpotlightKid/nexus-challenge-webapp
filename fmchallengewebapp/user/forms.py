# -*- coding: utf-8 -*-
"""User blueprint forms."""

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import Email, EqualTo, InputRequired, Length

from .models import User


class RegisterForm(FlaskForm):
    """User account registration form."""

    username = StringField('Username', validators=[InputRequired(), Length(min=3, max=25)])
    email = StringField('Email', validators=[InputRequired(), Email(), Length(min=6, max=40)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=40)])
    confirm = PasswordField('Repeat password',
        validators=[InputRequired(), EqualTo('password', message='Passwords must match')])

    def validate(self):
        """Validate the form."""
        initial_validation = super(RegisterForm, self).validate()
        if not initial_validation:
            return False

        user = User.query.filter_by(username=self.username.data).first()
        if user:
            self.username.errors.append('Username already registered')
            return False

        user = User.query.filter_by(email=self.email.data).first()
        if user:
            self.email.errors.append('Email already registered')
            return False

        return True


class LoginForm(FlaskForm):
    """Login authentication form."""

    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(LoginForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(LoginForm, self).validate()
        if not initial_validation:
            return False

        self.user = User.query.filter_by(username=self.username.data).first()
        if not self.user:
            self.username.errors.append('Unknown username')
            return False

        if not self.user.is_active:
            self.username.errors.append('User account deactivated')
            return False

        if not self.user.check_password(self.password.data):
            self.password.errors.append('Invalid password')
            return False

        if not self.user.is_confirmed:
            self.username.errors.append('Email confirmation for user account not completed')
            return False

        return True


class ForgotForm(FlaskForm):
    """Forgotten password reset request form."""

    email = StringField('Email',
        validators=[InputRequired(), Email(message=None), Length(min=6, max=255)])

    def validate(self):
        """Validate that a user with given email exists."""
        initial_validation = super(ForgotForm, self).validate()
        if not initial_validation:
            return False

        user = User.query.filter_by(email=self.email.data).first()
        if not user:
            self.email.errors.append('This email is not registered')
            return False

        return True


class ChangePasswordForm(FlaskForm):
    """Change password form."""

    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=255)])
    confirm = PasswordField('Repeat password',
        validators=[InputRequired(), EqualTo('password', message='Passwords must match')])
