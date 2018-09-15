# -*- coding: utf-8 -*-
"""User blueprint views."""

import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from fmchallengewebapp.extensions import login_manager

from .decorators import check_confirmed
from .email import send_email
from .forms import ChangePasswordForm, ForgotForm, LoginForm, RegisterForm
from .models import User
from .token import confirm_token, generate_confirmation_token

blueprint = Blueprint('user', __name__, url_prefix='/users', static_folder='../static')


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))


@blueprint.route('/')
@login_required
def members():
    """Landing page for authenticated users."""
    return render_template('users/members.html')


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user account registration form."""
    form = RegisterForm(request.form)

    if form.validate_on_submit():
        user = User.create(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            is_active=True,
            is_confirmed=False
        )
        token = generate_confirmation_token(user.email)
        confirm_url = url_for('user.confirm_email', token=token, _external=True)
        html = render_template('users/activate.html', confirm_url=confirm_url)
        subject = 'Please confirm your email'
        send_email(user.email, subject, html)
        login_user(user)

        flash('A confirmation email has been sent via email.', 'success')
        return redirect(url_for('user.unconfirmed'))

    return render_template('users/register.html', form=form)


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login form."""
    form = LoginForm(request.form)

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            flash('You are logged in.', 'success')
            return redirect(url_for('public.home'))
        else:
            flash('Invalid email and/or password.', 'danger')
            return render_template('users/login.html', form=form)

    return render_template('users/login.html', form=form)


@blueprint.route('/logout')
@login_required
def logout():
    """Handle use logout."""
    logout_user()
    flash('You were logged out.', 'success')
    return redirect(url_for('user.login'))


@blueprint.route('/profile', methods=['GET', 'POST'])
@login_required
@check_confirmed
def profile():
    """Handle user account update form."""
    form = ChangePasswordForm(request.form)

    if form.validate_on_submit():
        user = User.query.filter_by(email=current_user.username).first()

        if user:
            user.update(password=form.password.data)
            flash('Password successfully changed.', 'success')
            return redirect(url_for('user.profile'))
        else:
            flash('Password change was unsuccessful.', 'danger')
            return redirect(url_for('user.profile'))

    return render_template('users/profile.html', form=form)


@blueprint.route('/confirm/<token>')
@login_required
def confirm_email(token):
    """Handle request from confirmation email link."""
    if current_user.is_confirmed:
        flash('Account already confirmed. Please login.', 'success')
        return redirect(url_for('public.home'))

    email = confirm_token(token)
    user = User.query.filter_by(email=current_user.email).first_or_404()

    if user.email == email:
        user.update(is_confirmed=True, confirmed_on=datetime.datetime.now())
        flash('You have confirmed your account. Thanks!', 'success')
    else:
        flash('The confirmation link is invalid or has expired.', 'danger')

    return redirect(url_for('public.home'))


@blueprint.route('/unconfirmed')
@login_required
def unconfirmed():
    """Show page for for unconfirmed user accounts."""
    if current_user.is_confirmed:
        return redirect(url_for('public.home'))

    flash('Please confirm your account!', 'warning')
    return render_template('users/unconfirmed.html')


@blueprint.route('/resend')
@login_required
def resend_confirmation():
    """Re-send user account confirmation email."""
    token = generate_confirmation_token(current_user.email)
    confirm_url = url_for('user.confirm_email', token=token, _external=True)
    html = render_template('users/activate.html', confirm_url=confirm_url)
    subject = 'Please confirm your email'
    send_email(current_user.email, subject, html)
    flash('A new confirmation email has been sent.', 'success')
    return redirect(url_for('user.unconfirmed'))


@blueprint.route('/forgot', methods=['GET', 'POST'])
def forgot():
    """Handle forgotten password form."""
    form = ForgotForm(request.form)

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        token = generate_confirmation_token(user.email)
        reset_url = url_for('user.forgot_new', token=token, _external=True)
        html = render_template('users/reset.html', username=user.email, reset_url=reset_url)
        subject = 'Reset your password'
        send_email(user.email, subject, html)
        user.update(password_reset_token=token)
        flash('A password reset email has been sent via email.', 'success')
        return redirect(url_for('public.home'))

    return render_template('users/forgot.html', form=form)


@blueprint.route('/forgot/new/<token>', methods=['GET', 'POST'])
def forgot_new(token):
    """Handle update forgotten password form."""
    email = confirm_token(token)
    user = User.query.filter_by(email=email).first_or_404()

    if user.password_reset_token is not None:
        form = ChangePasswordForm(request.form)

        if form.validate_on_submit():
            user = User.query.filter_by(email=email).first()

            if user:
                user.update(password=form.password.data, password_reset_token=None)
                login_user(user)
                flash('Password successfully changed.', 'success')
                return redirect(url_for('user.profile'))

            else:
                flash('Password change was unsuccessful.', 'danger')
                return redirect(url_for('user.profile'))
        else:
            flash('You can now change your password.', 'success')
            return render_template('users/forgot_new.html', form=form)
    else:
        flash('Can not reset the password, try again.', 'danger')

    return redirect(url_for('public.home'))
