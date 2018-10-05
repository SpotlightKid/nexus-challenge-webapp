# -*- coding: utf-8 -*-
"""Public blueprint views."""

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_user

from fmchallengewebapp.user.forms import LoginForm
from fmchallengewebapp.utils import flash_errors

blueprint = Blueprint('public', __name__, static_folder='../static')


@blueprint.route('/', methods=['GET', 'POST'])
def home():
    """Home page."""
    form = LoginForm(request.form)
    # Handle logging in
    if request.method == 'POST':
        if form.validate_on_submit():
            login_user(form.user)
            flash('You are logged in.', 'success')
            redirect_url = request.args.get('next') or url_for('user.members')
            return redirect(redirect_url)
        else:
            flash_errors(form)

    return render_template('public/home.html', page_title='Start', login_form=form)


@blueprint.route('/about/')
def about():
    """About page."""
    form = LoginForm(request.form)
    return render_template('public/about.html', page_title='About', login_form=form)
