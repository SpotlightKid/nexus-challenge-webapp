# -*- coding: utf-8 -*-
"""Public blueprint views."""

import random
from datetime import datetime
from operator import attrgetter, itemgetter

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from fmchallengewebapp.user.decorators import check_confirmed, check_is_admin
from fmchallengewebapp.user.email import start_send_email_task
from fmchallengewebapp.utils import (archiveorg_player, canonify_track_url, in_submission_period,
                                     in_voting_period, to_bool)

from .forms import SubmitCompetitionEntryForm, VotingForm
from .models import CompetitionEntry, Vote

blueprint = Blueprint('competition', __name__, static_folder='../static')


# utility functions for this module
def get_user_votes(user):
    votes = {}
    for vote in Vote.query.filter(Vote.user_id == user.id, Vote.points > 0):
        key = VotingForm.points_to_fields.get(vote.points)
        if key:
            votes[key] = vote.entry_id
    return votes


# template context processsors
@blueprint.context_processor
def inject_player():
    return dict(
        archiveorg_player=archiveorg_player,
    )


# request handlers
@blueprint.route('/vote/')
def vote():
    now = datetime.utcnow()
    entries = CompetitionEntry.query.filter_by(is_approved=True)
    order = request.args.get('order')
    desc = to_bool(request.args.get('desc'))

    if order in ('artist', 'title', 'published_on'):
        entries = sorted(entries, key=attrgetter(order), reverse=desc)
    else:
        entries = list(entries)
        random.shuffle(entries)

    if current_user.is_authenticated:
        user_votes = Vote.query.filter_by(user_id=current_user.id)
        user_votes = user_votes.order_by(Vote.points.desc()).limit(5)
    else:
        user_votes = None

    return render_template(
        'competition/vote.html',
        desc=desc,
        entries=entries,
        in_submission_period=in_submission_period(now),
        in_voting_period=in_voting_period(now),
        now=now,
        order=order,
        user_votes=user_votes
    )



@blueprint.route('/submit_vote', methods=['GET', 'POST'])
@login_required
@check_confirmed
def submit_vote():
    """Vote submission form page."""
    # check whether voting is attempted outside of competition voting period
    now = datetime.utcnow()
    start_date = current_app.config.get('VOTING_PERIOD_START')
    end_date = current_app.config.get('VOTING_PERIOD_END')

    if start_date and now < start_date:
        flash("The voting period of the competition has not begun yet. "
              "No votes can be submitted at this time.", 'danger')
        return redirect(url_for('competition.vote'))
    elif end_date and now >= end_date:
        flash("The voting period of the competition is over. "
              "Votes cannot be submitted anymore.", 'danger')
        return redirect(url_for('competition.vote'))

    entries = CompetitionEntry.query.filter(
        CompetitionEntry.is_approved == True,  # noqa:E712
        CompetitionEntry.user_id != current_user.id
    )
    entries = [(entry.id, '“{}” by {}'.format(entry.title, entry.artist)) for entry in entries]
    entry_ids = [entry[0] for entry in entries]
    entries.sort(key=itemgetter(1))

    current_votes = get_user_votes(current_user)

    if current_votes:
        form = VotingForm(request.form, **current_votes)
        submit_label = "Submit Vote!"
        meta_title = "Update Vote"
    else:
        # Bogus entry for empty first option of selects
        entries.insert(0, (-1, ""))
        form = VotingForm(request.form, **current_votes)
        submit_label = "Submit Vote!"
        meta_title = "Submit Vote"

    form.first.choices = entries
    # set allowed values for AnyOf validator shared by all select fields
    form.first.validators[1].values = entry_ids
    form.second.choices = entries
    form.third.choices = entries
    form.fourth.choices = entries
    form.fifth.choices = entries

    if form.validate_on_submit():
        for points, field in VotingForm.points_to_fields.items():
            vote = Vote.query.filter_by(user_id=current_user.id, points=points).first()
            entry_id = getattr(form, field).data

            if vote and vote.entry_id == entry_id:
                current_app.logger.debug("Not updating unchanged vote: %r", vote)
            elif vote:
                current_app.logger.debug("Updating vote: %r.", vote)
                vote.update(entry_id=entry_id, created_on=now)
                current_app.logger.debug("New entry: %r", vote.entry)
            else:
                vote = Vote.create(user_id=current_user.id, entry_id=entry_id, points=points,
                                   created_on=now)
                current_app.logger.debug("Created new vote: %r", vote)

        if current_votes:
            flash("Your vote was successfully updated. Thank you for voting!", 'success')
        else:
            flash("Your vote was registered successfully. Thank you for voting!", 'success')
        return redirect(url_for('competition.vote'))
    else:
        return render_template(
            'competition/submit_vote.html',
            form=form,
            submit_label=submit_label,
            meta_title=meta_title
        )


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
    # check whether submission is attempted outside of competition submission period
    now = datetime.utcnow()
    start_date = current_app.config.get('SUBMISSION_PERIOD_START')
    end_date = current_app.config.get('SUBMISSION_PERIOD_END')

    if start_date and now < start_date:
        flash("The competition submission period has not begun yet. "
              "Entries cannot be submitted or updated at this time.", 'danger')
        return redirect(url_for('competition.manage_entry'))
    elif end_date and now >= end_date:
        flash("The competition submission period is over. "
              "Entries cannot be submitted or updated anymore.", 'danger')
        return redirect(url_for('competition.manage_entry'))

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
                flash("Your competition entry is already published "
                      "and can't be updated anymore.", 'danger')
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
                html = render_template('competition/notify_create.html', view_url=view_url,
                    entry=user_entry, user=current_user)
                subject = 'New competition submission by {}'.format(current_user.username)
                start_send_email_task(current_app.config['SITE_ADMIN_EMAIL'], subject, html)
            except Exception:
                current_app.logger.exception("Error sending entry creation notification.")
            else:
                flash("You successfully created a competition entry.", 'success')

        return redirect(url_for('competition.manage_entry'))
    else:
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
    # check whether publication is attempted outside of competition submission period
    now = datetime.utcnow()
    start_date = current_app.config.get('SUBMISSION_PERIOD_START')
    end_date = current_app.config.get('SUBMISSION_PERIOD_END')

    if start_date and now < start_date:
        flash("The competition submission period has not begun yet. "
              "No entries can be published at this time.", 'danger')
        return redirect(url_for('competition.manage_entry'))
    elif end_date and now >= end_date:
        flash("The competition submission period is over. "
              "No entries can be published anymore.", 'danger')
        return redirect(url_for('competition.manage_entry'))

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
                        user=current_user
                    )
                    subject = 'Competition entry published by {}'.format(current_user.username)
                    start_send_email_task(
                        current_app.config['SITE_ADMIN_EMAIL'],
                        subject,
                        html
                    )
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
    now = datetime.utcnow()
    user_entry = None

    if current_user.is_authenticated:
        user_entry = CompetitionEntry.query.filter_by(user_id=current_user.id).first()

    meta_title = "Review Competition Entry" if user_entry else "Enter the Competition"
    return render_template(
        'competition/manage.html',
        entry=user_entry,
        in_submission_period=in_submission_period(now),
        meta_title=meta_title,
        now=now
    )


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
