# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""

from flask import current_app, flash


def flash_errors(form, category='warning'):
    """Flash all errors for a form."""
    if len(form.errors) > 1:
        msgfmt = '{field} - {msg}'
    else:
        msgfmt = '{msg}'

    for field, errors in form.errors.items():
        for error in errors:
            flash(msgfmt.format(field=getattr(form, field).label.text, msg=error), category)


def inject_site_info():
    return dict(
        navigation_links=current_app.config.get('NAVIGATION_LINKS', []),
        site_title=current_app.config.get('SITE_TITLE'),
        site_email=current_app.config.get('SITE_EMAIL'),
        site_description=current_app.config.get('SITE_DESCRIPTION'),
        site_url=current_app.config.get('SITE_URL'),
        site_author=current_app.config.get('SITE_AUTHOR'),
    )
