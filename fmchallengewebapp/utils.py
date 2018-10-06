# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""

from posixpath import basename
from urllib.parse import urlparse

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


def format_duration(sec):
    return "%02i:%02i" % (int(sec / 60), sec % 60)


def canonify_track_url(url):
    track_id = url.strip()
    if track_id.startswith(('http', 'archive.org')):
        urlparts = urlparse(track_id)
        track_id = basename(urlparts.path)
    url = 'https://archive.org/details/' + track_id
    return url, track_id