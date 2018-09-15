# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""

from flask import flash


def flash_errors(form, category='warning'):
    """Flash all errors for a form."""
    if len(form.errors) > 1:
        msgfmt = '{field} - {msg}'
    else:
        msgfmt = '{msg}'

    for field, errors in form.errors.items():
        for error in errors:
            flash(msgfmt.format(field=getattr(form, field).label.text, msg=error), category)
