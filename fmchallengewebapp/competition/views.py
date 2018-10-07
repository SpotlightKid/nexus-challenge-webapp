# -*- coding: utf-8 -*-
"""Public blueprint views."""

from datetime import datetime
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from fmchallengewebapp.utils import archiveorg_player, canonify_track_url
from fmchallengewebapp.user.decorators import check_is_admin, check_confirmed
from fmchallengewebapp.user.email import start_send_email_task

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
                flash("Your competition entry is already published and can't be updated anymore.",
                      'danger')
            else:
                user_entry.update(
                    title=form.title.data.strip(),
                    artist=form.artist.data.strip(),
                    url=url,
                    description=form.description.data.strip(),
                    production_details=form.production_details.data.strip(),
                    last_modified_on=datetime.utcnow()
                )
                flash("Your competition entry was successfully updated.", 'success')
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
            flash("You successfully created a competition entry.", 'success')

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
            flash("Your competition entry is already published.", 'info')
        else:
            confirm = request.args.get('confirm', False)
            if confirm and str(confirm).lower() in ('1', 'yes', 'true'):
                user_entry.update(
                    is_published=True,
                    published_on=datetime.utcnow()
                )
                try:
                    approve_url = url_for('competition.approve', entry=user_entry.id,
                                          _external=True)
                    html = render_template(
                        'competition/notify_publish.html',
                        approve_url=approve_url,
                        entry=user_entry,
                        user=current_user)
                    subject = 'New competition submission by {}'.format(current_user.username)
                    start_send_email_task(current_app.config['SITE_ADMIN_EMAIL'], subject, html)
                except Exception:
                    current_app.logger.exception("Error sending entry pubublish notification.")
                    flash(("Your competition entry was published successfully, but there "
                           "was an error while sending a notification to the organizer. "
                           "Please contact <{}> to make sure your entry is approved "
                           "soon.").format(current_app.config['SITE_EMAIL']), 'warning')
                else:
                    flash("Your competition entry was published successfully!", 'success')
            else:
                return render_template('competition/publish_confirm.html')
    else:
        flash("You have not submitted a competition entry yet.", 'warning')

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


@blueprint.route('/approve/<int:entry>')
@login_required
@check_is_admin
def approve(entry):
    entry = CompetitionEntry.get_by_id(entry)
    if not entry:
        flash("Competition entry not found.", 'warning')
        return redirect(url_for('public.home'))

    confirm = request.args.get('confirm', False)
    if confirm and str(confirm).lower() in ('1', 'yes', 'true'):
        entry.update(is_approved=True)
        flash("The competition entry was approved!", 'success')

    return render_template('competition/approve.html', entry=entry)
