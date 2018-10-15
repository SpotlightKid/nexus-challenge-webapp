# -*- coding: utf-8 -*-
"""User blueprint forms."""

# Standard library modules
import re
from urllib.parse import urljoin, urlparse

# Third-party modules
from flask import redirect, request, url_for
from flask_wtf import FlaskForm
from wtforms import HiddenField, PasswordField, StringField
from wtforms.validators import Email, EqualTo, InputRequired, Length

from fmchallengewebapp.rules import rules
from .models import User


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def get_redirect_target():
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target


class RedirectForm(FlaskForm):
    next = HiddenField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.next.data:
            self.next.data = get_redirect_target() or ''

    def redirect(self, endpoint='index', **values):
        if is_safe_url(self.next.data):
            return redirect(self.next.data)
        target = get_redirect_target()
        return redirect(target or url_for(endpoint, **values))


class RegisterForm(FlaskForm):
    """User account registration form."""

    username = StringField('Username', validators=[InputRequired(), Length(min=3, max=25)])
    email = StringField('Email', validators=[InputRequired(), Email(), Length(min=6, max=40)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=40)])
    confirm = PasswordField('Repeat password',
        validators=[InputRequired(), EqualTo('password', message='Passwords must match')])
    captcha_challenge = HiddenField(validators=[InputRequired()])
    captcha_answer = StringField(description="Enter the word in all lowercase",
                                 validators=[InputRequired(), Length(min=1, max=20)])

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

        try:
            section, rule, word = self.captcha_challenge.data.split('-', 2)
            rule = int(rule)
            word = int(word)
            if word <= 0:
                raise ValueError
        except (AttributeError, IndexError, TypeError, ValueError):
            self.captcha_answer.errors.append('Invalid captcha challenge')
            return False

        answer = self.captcha_answer.data.strip().lower()
        if not self.verify_captcha(answer, section, rule, word - 1):
            self.captcha_answer.errors.append('Incorrect captcha answer')
            return False

        return True

    def verify_captcha(self, answer, section, rule, word):
        to_space = '(),.:;'
        xlate_table = str.maketrans(to_space, ' ' * len(to_space), '1234567890"\'\n-_')
        try:
            rule = rules[section][rule].strip().lower()
            rule = re.sub(r'\w+://[a-z/.]+', '', rule)
            rule = rule.translate(xlate_table)
            egg = rule.split()[word]
            return answer == egg
        except (IndexError, KeyError, TypeError, ValueError):
            return False


class LoginForm(RedirectForm):
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
