# -*- coding: utf-8 -*-
"""User blueprint email confirmation token handling."""

from flask import current_app
from itsdangerous import BadData, URLSafeTimedSerializer


def generate_confirmation_token(email):
    """Generate token for user account confirmation email."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token, expiration=3600):
    """Return email address saved in token."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        return serializer.loads(token, salt=current_app.config['SECURITY_PASSWORD_SALT'],
                                max_age=expiration)
    except BadData:
        return False
