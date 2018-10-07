# -*- coding: utf-8 -*-
"""User blueprint custom view decorators."""

from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def check_confirmed(func):
    """View decorator to check if account of current user has been confirmed."""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.is_confirmed is False:
            flash('Please confirm your account!', 'warning')
            return redirect(url_for('user.unconfirmed'))

        return func(*args, **kwargs)

    return decorated_function


def check_is_admin(func):
    """View decorator to check if account of current user is an admin."""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.is_admin is False:
            flash('Your account does not have permission to access this page.', 'warning')
            return redirect(url_for('user.login'))

        return func(*args, **kwargs)

    return decorated_function
