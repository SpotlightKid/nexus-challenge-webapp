# -*- coding: utf-8 -*-
"""Competition blueprint forms."""

from internetarchive import get_item
from flask import current_app
from flask_wtf import FlaskForm
from flask_pagedown.fields import PageDownField
from wtforms import BooleanField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, InputRequired, Length

from fmchallengewebapp.utils import canonify_track_url, format_duration
from .models import CompetitionEntry


class SubmitCompetitionEntryForm(FlaskForm):
    """Login authentication form."""

    title = StringField(
        'Title',
        description="The title of your track",
        validators=[InputRequired(), Length(min=2, max=100)])
    artist = StringField(
        'Artist',
        description="The name of the artist",
        validators=[InputRequired(), Length(min=2, max=100)])
    url = StringField(
        'URL',
        description='The URL or ID of the track on Archive.org, '
                    'e.g. "https://archive.org/details/MyTrack" or "MyTrack"',
        validators=[InputRequired(), Length(min=2, max=255)])
    description = PageDownField(
        'Description',
        description="Describe your track here, e.g. "
                    "mood, style, background story, etc. (Markdown allowed).",
        validators=[InputRequired(), Length(min=10, max=1000)])
    production_details = PageDownField(
        'Production Details',
        description="List all software you used to make the track here (Markdown allowed).",
        validators=[InputRequired(), Length(min=10, max=1000)])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super().__init__(*args, **kwargs)

    def add_form_error(self, msg):
        self.errors.setdefault('form', []).append(msg)

    def validate(self):
        """Validate the form."""
        initial_validation = super().validate()
        if not initial_validation:
            return False

        url, track_id = canonify_track_url(self.url.data)

        error = False
        try:
            item = get_item(track_id, request_kwargs={'timeout': 30})
            metadata = item.item_metadata.get('metadata')
            if not metadata:
                raise ValueError("'%s' not found." % track_id)
        except Exception as exc:
            self.add_form_error("Could not get meta data from Archive.org: %s" % exc)
            error = True
        else:
            if metadata.get('title', '').strip().lower() != self.title.data.strip().lower():
                self.add_form_error("Title does not match title in Archive.org meta data.")
                error = True

            if metadata.get('creator', '').strip().lower() != self.artist.data.strip().lower():
                self.add_form_error("Artist does not match creator/author in Archive.org meta data.")

            flac = None
            for file in getattr(item, 'files', []):
                if file.get('format') == 'Flac':
                    flac = file
                    break
            else:
                self.add_form_error("Track not available in FLAC format.")
                error = True

            if flac:
                try:
                    length = float(flac.get('length', 0))
                except (TypeError, ValueError):
                    length = 0

                min_length = current_app.config.get('MIN_TRACK_LENGTH', 60.0)
                max_length = current_app.config.get('MAX_TRACK_LENGTH', 300.0)

                if length < min_length:
                    self.add_form_error("Track does not have minimum required duration (%s min.)."
                                        % format_duration(min_length))
                    error = True
                elif length > max_length:
                    self.add_form_error("Track exceeds maximum allowed duration (%s min.)." %
                                        format_duration(max_length))
                    error = True
            else:
                self.add_form_error("Missing meta data for FLAC download of track.")
                error = True

        return not error
