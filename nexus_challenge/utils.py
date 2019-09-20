# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""

# Standard library modules
from posixpath import basename
from urllib.parse import urlencode, urlparse

# Third-party modules
from flask import current_app, flash, render_template


TMPL_IFRAME = """\
<iframe class="archiveorg-player"
  src="{url}"
  width="{width}" height="{height}" frameborder="0"
  allowfullscreen webkitallowfullscreen="true" mozallowfullscreen="true">
</iframe>
<p class="alert alert-primary">If you do not see the audio player here, please allow JavaScript
and Iframe embedding from archive.org.</p>
"""


def archiveorg_player(url, **options):
    """Generate HTML snippet to embed archive.org audio / video player."""
    options = options or {}
    opts = {
        'id': 'archiveorg_player',
        'width': 640,
        'height': 580 if 'playlist' in options else 45,
        'compat_info': True,
    }
    opts.update(options)
    params = {}

    if opts.get("autoplay"):
        params['autoplay'] = '1'

    if opts.get("playlist"):
        params['playlist'] = '1'

    if "list_height" in opts:
        params['list_height'] = str(opts['list_height'])

    if "poster" in opts:
        params['poster'] = opts['poster']

    url = "https://archive.org/embed/" + canonify_track_url(url)[1]

    if params:
        url += '?' + urlencode(params)

    return render_template('archiveorgplayer.html', url=url, **opts)


def canonify_track_url(url):
    track_id = url.strip()
    if track_id.startswith(('http', 'archive.org')):
        urlparts = urlparse(track_id)
        track_id = basename(urlparts.path)
    url = 'https://archive.org/details/' + track_id
    return url, track_id


def flash_errors(form, category='warning'):
    """Flash all errors for a form."""
    if len(form.errors) > 1:
        msgfmt = '{field} - {msg}'
    else:
        msgfmt = '{msg}'

    for field, errors in form.errors.items():
        for error in errors:
            flash(msgfmt.format(field=getattr(form, field).label.text, msg=error), category)


def format_duration(sec):
    return "%02i:%02i" % (int(sec / 60), sec % 60)


def in_submission_period(now):
    start_date = current_app.config.get('SUBMISSION_PERIOD_START')
    end_date = current_app.config.get('SUBMISSION_PERIOD_END')
    return (start_date is None or now >= start_date) and (end_date is None or now < end_date)


def in_voting_period(now):
    start_date = current_app.config.get('VOTING_PERIOD_START')
    end_date = current_app.config.get('VOTING_PERIOD_END')
    return (start_date is None or now >= start_date) and (end_date is None or now < end_date)


def inject_site_info():
    return dict(
        navigation_links=current_app.config.get('NAVIGATION_LINKS', []),
        site_title=current_app.config.get('SITE_TITLE'),
        site_email=current_app.config.get('SITE_EMAIL'),
        site_description=current_app.config.get('SITE_DESCRIPTION'),
        site_url=current_app.config.get('SITE_URL'),
        site_author=current_app.config.get('SITE_AUTHOR'),
        submission_start=current_app.config.get('SUBMISSION_PERIOD_START'),
        submission_end=current_app.config.get('SUBMISSION_PERIOD_END'),
        voting_start=current_app.config.get('VOTING_PERIOD_START'),
        voting_end=current_app.config.get('VOTING_PERIOD_END'),
    )


def to_bool(val, true_values=('1', 'on', 't', 'true', 'y', 'yes')):
    return str(val).strip().lower() in true_values
