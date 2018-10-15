# -*- coding: utf-8 -*-
"""Competition blueprint forms."""

# Third-party modules
from flask import current_app
from flask_login import current_user
from flask_pagedown.fields import PageDownField
from flask_wtf import FlaskForm
from internetarchive import get_item
from wtforms import SelectField, StringField
from wtforms.validators import AnyOf, InputRequired, Length

# Application specific modules
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

        try:
            item = get_item(track_id, request_kwargs={'timeout': 30})
            metadata = item.item_metadata.get('metadata')
            if not metadata:
                raise ValueError("'%s' not found." % track_id)
        except Exception as exc:
            self.add_form_error("Could not get meta data from Archive.org: %s" % exc)
        else:
            if metadata.get('title', '').strip().lower() != self.title.data.strip().lower():
                self.add_form_error("Title does not match title in Archive.org meta data.")

            if metadata.get('creator', '').strip().lower() != self.artist.data.strip().lower():
                self.add_form_error("Artist does not match creator / author "
                                    "in Archive.org meta data.")

            flac = None
            for file in getattr(item, 'files', []):
                if file.get('format') == 'Flac':
                    flac = file
                    break
            else:
                self.add_form_error("Track not available in FLAC format.")

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
                elif length > max_length:
                    self.add_form_error("Track exceeds maximum allowed duration (%s min.)." %
                                        format_duration(max_length))
            else:
                self.add_form_error("Missing meta data for FLAC download of track.")

        return not self.errors.get('form')


vote_validators = [InputRequired(), AnyOf([-1], message="You must select an entry.")]


class VotingForm(FlaskForm):
    """Form for voting on competition entries."""

    points_to_fields = {
        5: 'first',
        4: 'second',
        3: 'third',
        2: 'fourth',
        1: 'fifth'
    }
    fields_to_points = {v: k for k, v in points_to_fields.items()}

    first = SelectField('5 points to:', coerce=int, validators=vote_validators)
    second = SelectField('4 points to:', coerce=int, validators=vote_validators)
    third = SelectField('3 points to:', coerce=int, validators=vote_validators)
    fourth = SelectField('2 points to:', coerce=int, validators=vote_validators)
    fifth = SelectField('1 point to:', coerce=int, validators=vote_validators)

    def add_form_error(self, msg):
        self.errors.setdefault('form', []).append(msg)

    def validate(self):
        """Validate the form."""
        initial_validation = super().validate()
        if not initial_validation:
            return False

        votes = {k: v for k, v in self.data.items() if k in self.fields_to_points}

        if len(set(votes.values())) < len(votes):
            self.add_form_error("You must select five different competition entries.")

        user_entry = CompetitionEntry.query.filter_by(user_id=current_user.id).first()
        if user_entry:
            for field, entry_id in votes.items():
                if entry_id == user_entry.id:
                    self.add_form_error("You may not vote for your own competition entry.")

        return not self.errors.get('form')
