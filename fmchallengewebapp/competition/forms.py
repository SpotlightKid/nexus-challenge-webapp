# -*- coding: utf-8 -*-
"""Competition blueprint forms."""

from flask_wtf import FlaskForm
from flask_pagedown.fields import PageDownField
from wtforms import BooleanField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length

from .models import CompetitionEntry



class SubmitCompetitionEntryForm(FlaskForm):
    """Login authentication form."""

    title = StringField(
        'Title',
        description="The title of your track",
        validators=[DataRequired()])
    artist = StringField(
        'Artist',
        description="The name of the artist",
        validators=[DataRequired()])
    url = StringField(
        'URL',
        description="The URL of the track on archive.org",
        validators=[DataRequired()])
    description = PageDownField(
        'Description',
        description="Describe your track here, e.g. mood, style, background story, etc. (Markdown allowed).",
        validators=[DataRequired()])
    production_details = PageDownField(
        'Production Details',
        description="List all software you used to make the track here (Markdown allowed).",
        validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super().__init__(*args, **kwargs)

    def validate(self):
        """Validate the form."""
        initial_validation = super().validate()
        if not initial_validation:
            return False

        return True
