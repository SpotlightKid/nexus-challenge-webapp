# -*- coding: utf-8 -*-
"""Public blueprint views."""

from datetime import datetime
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from fmchallengewebapp.utils import archiveorg_player, canonify_track_url, flash_errors
from fmchallengewebapp.user.decorators import check_confirmed

from .forms import SubmitCompetitionEntryForm
from .models import CompetitionEntry


blueprint = Blueprint('competition', __name__, static_folder='../static')


@blueprint.context_processor
def inject_player():
    return dict(
        archiveorg_player=archiveorg_player,
    )


@blueprint.route('/submit_entry', methods=['GET', 'POST'])
@login_required
@check_confirmed
def submit_entry():
    """Competition entry submission form page."""
    user_entry = CompetitionEntry.query.filter_by(user_id=current_user.id).first()
    if user_entry:
        form = SubmitCompetitionEntryForm(request.form, obj=user_entry)
        submit_label = "Update Draft!"
        meta_title = "Update Competition Entry"
    else:
        form = SubmitCompetitionEntryForm(request.form)
        submit_label = "Create Draft!"
        meta_title = "Submit Competition Entry"

    if form.validate_on_submit():
        url, _ = canonify_track_url(form.url.data)
        if user_entry:
            if user_entry.is_published:
                flash("Your competition entry is already published and can't be updated anymore.")
            user_entry.update(
                title=form.title.data.strip(),
                artist=form.artist.data.strip(),
                url=url,
                description=form.description.data.strip(),
                production_details=form.production_details.data.strip(),
                last_modified_on=datetime.utcnow()
            )
        else:
            CompetitionEntry.create(
                title=form.title.data.strip(),
                artist=form.artist.data.strip(),
                url=url,
                description=form.description.data.strip(),
                production_details=form.production_details.data.strip(),
                last_modified_on=datetime.utcnow(),
                user_id=current_user.id
            )

        return redirect(url_for('competition.view_entry'))

    return render_template(
        'competition/submit.html',
        form=form,
        meta_title=meta_title,
        submit_label=submit_label
    )


@blueprint.route('/publish_entry')
@login_required
@check_confirmed
def publish_entry():
    """Publish a competition entry."""
    user_entry = CompetitionEntry.query.filter_by(user_id=current_user.id).first()
    if user_entry:
        if user_entry.is_published:
            flash("Your competition entry is already published.")
        else:
            confirm = request.args.get('confirm', False)
            if confirm and str(confirm).lower() in ('1', 'yes', 'true'):
                user_entry.update(
                    is_published=True,
                    published_on=datetime.utcnow()
                )
            else:
                return render_template('competition/publish_confirm.html')
    else:
        flash("You have not submitted a competition entry yet.")

    return redirect(url_for('competition.view_entry'))


@blueprint.route('/submit/')
def view_entry():
    user_entry = None
    if current_user.is_authenticated:
        user_entry = CompetitionEntry.query.filter_by(user_id=current_user.id).first()

    meta_title = "Review Competition Entry" if user_entry else "Enter the Competition"
    return render_template(
        'competition/view.html',
        meta_title=meta_title,
        user_entry=user_entry)
