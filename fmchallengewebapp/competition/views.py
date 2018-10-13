# -*- coding: utf-8 -*-
"""Public blueprint views."""

import random
from operator import attrgetter
from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from fmchallengewebapp.utils import archiveorg_player, canonify_track_url, to_bool
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


@blueprint.route('/vote/')
def vote():
    entries = CompetitionEntry.query.filter_by(is_approved=True)
    order = request.args.get('order')
    desc = to_bool(request.args.get('desc'))

    if order in ('artist', 'title', 'published_on'):
        entries = sorted(entries, key=attrgetter(order), reverse=desc)
    else:
        entries = list(entries)
        random.shuffle(entries)

    return render_template('competition/vote.html', entries=entries, order=order, desc=desc)


@blueprint.route('/list/')
def list_entries():
    if current_user.is_authenticated and current_user.is_admin:
        entries = CompetitionEntry.query.all()
    else:
        entries = CompetitionEntry.query.filter_by(is_approved=True)

    order = request.args.get('order')
    desc = to_bool(request.args.get('desc'))

    if order in ('artist', 'title', 'published_on'):
        if order == 'published_on':
            def key_func(obj):
                return obj.published_on or datetime.min
        else:
            key_func = attrgetter(order)
        entries = sorted(entries, key=key_func, reverse=desc)
    else:
        entries = list(entries)
        random.shuffle(entries)

    return render_template('competition/list.html', entries=entries, order=order, desc=desc)


@blueprint.route('/view/<int:entry>')
def view_entry(entry):
    entry = CompetitionEntry.get_by_id(entry)
    if not entry or not entry.is_approved:
        flash("Competition entry not found.", 'warning')
        return redirect(url_for('public.home'))

    return render_template('competition/view.html', entry=entry)


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
            user_entry = CompetitionEntry.create(
                title=form.title.data.strip(),
                artist=form.artist.data.strip(),
                url=url,
                description=form.description.data.strip(),
                production_details=form.production_details.data.strip(),
                last_modified_on=datetime.utcnow(),
                user_id=current_user.id
            )
            try:
                view_url = url_for('competition.approve', entry=user_entry.id,
                                   _external=True, _scheme='https')
                html = render_template(
                    'competition/notify_create.html',
                    view_url=view_url,
                    entry=user_entry,
                    user=current_user)
                subject = 'New competition submission by {}'.format(current_user.username)
                start_send_email_task(current_app.config['SITE_ADMIN_EMAIL'], subject, html)
            except Exception:
                current_app.logger.exception("Error sending entry creation notification.")
            else:
                flash("You successfully created a competition entry.", 'success')

        return redirect(url_for('competition.manage_entry'))

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
            confirm = to_bool(request.args.get('confirm'))
            if confirm:
                user_entry.update(
                    is_published=True,
                    published_on=datetime.utcnow()
                )
                try:
                    approve_url = url_for('competition.approve', entry=user_entry.id,
                                          _external=True, _scheme='https')
                    html = render_template(
                        'competition/notify_publish.html',
                        approve_url=approve_url,
                        entry=user_entry,
                        user=current_user)
                    subject = 'Competition entry published by {}'.format(current_user.username)
                    start_send_email_task(current_app.config['SITE_ADMIN_EMAIL'], subject, html)
                except Exception:
                    current_app.logger.exception("Error sending entry publish notification.")
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

    return redirect(url_for('competition.manage_entry'))


@blueprint.route('/submit/')
def manage_entry():
    user_entry = None
    if current_user.is_authenticated:
        user_entry = CompetitionEntry.query.filter_by(user_id=current_user.id).first()

    meta_title = "Review Competition Entry" if user_entry else "Enter the Competition"
    return render_template(
        'competition/manage.html',
        meta_title=meta_title,
        entry=user_entry)


@blueprint.route('/approve/<int:entry>')
@login_required
@check_is_admin
def approve(entry):
    entry = CompetitionEntry.get_by_id(entry)
    if not entry:
        flash("Competition entry not found.", 'warning')
        return redirect(url_for('public.home'))

    confirm = to_bool(request.args.get('confirm'))
    if confirm:
        entry.update(is_approved=True)
        try:
            view_url = url_for('competition.view_entry', entry=entry.id,
                               _external=True, _scheme='https')
            html = render_template(
                'competition/notify_approve.html',
                view_url=view_url,
                entry=entry,
                user=current_user,
                approved_on=datetime.utcnow())
            subject = 'Your FM Challenge competition entry has been approved'
            start_send_email_task(entry.user.email, subject, html)
        except Exception:
            current_app.logger.exception("Error sending entry approval notification.")
            flash(("The competition entry was approved successfully, but there "
                   "was an error while sending a notification to the user. "
                   "Please contact <{}> to let the user know the entry is approved."
                   ).format(entry.user.email), 'warning')
        else:
            flash("The competition entry was approved!", 'success')

    return render_template('competition/approve.html', entry=entry)
