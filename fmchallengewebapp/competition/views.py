# -*- coding: utf-8 -*-
"""Public blueprint views."""

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from fmchallengewebapp.utils import flash_errors
from fmchallengewebapp.user.decorators import check_confirmed

from .forms import SubmitCompetitionEntryForm


blueprint = Blueprint('competition', __name__, static_folder='../static')


@blueprint.route('/submit/')
def submit_entry():
    """Competition entry submission form page."""
    if current_user.is_authenticated:
        form = SubmitCompetitionEntryForm(request.form)
        if form.validate_on_submit():
            redirect(url_for('competition.view_entry'))
        return render_template(
            'competition/submit.html',
            form=form,
            page_title="Submit Competition Entry",
            submit_label="Create Draft!")
    else:
        return render_template(
            'competition/submit_nologin.html',
            page_title="Submit Competition Entry")


@blueprint.route('/submission')
@login_required
@check_confirmed
def view_entry():
    return render_template(
        'competition/view.html',
        page_title="Review Competition Entry")
