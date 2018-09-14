# -*- coding: utf-8 -*-
# fmchallengewebapp/user/views.py
"""User views."""

import datetime

from flask import render_template, Blueprint, url_for, render_template, redirect, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from ..database import db

from .models import User
from .email import send_email
from .token import generate_confirmation_token, confirm_token
from .decorators import check_confirmed
from .forms import LoginForm, RegisterForm, ChangePasswordForm, ForgotForm


blueprint = Blueprint('user', __name__, url_prefix='/users', static_folder='../static')


@blueprint.route('/')
@login_required
def members():
    """List members."""
    return render_template('users/members.html')


################
#### routes ####
################

@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        user = User.create(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            confirmed=False
        )
        db.session.add(user)
        db.session.commit()

        token = generate_confirmation_token(user.email)
        confirm_url = url_for('user.confirm_email', token=token, _external=True)
        html = render_template('users/activate.html', confirm_url=confirm_url)
        subject = "Please confirm your email"
        send_email(user.email, subject, html)

        login_user(user)

        flash('A confirmation email has been sent via email.', 'success')
        return redirect(url_for("user.unconfirmed"))

    return render_template('users/register.html', form=form)


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            flash('Welcome.', 'success')
            return redirect(url_for('public.home'))
        else:
            flash('Invalid email and/or password.', 'danger')
            return render_template('users/login.html', form=form)
    return render_template('users/login.html', form=form)


@blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You were logged out.', 'success')
    return redirect(url_for('user.login'))


@blueprint.route('/profile', methods=['GET', 'POST'])
@login_required
@check_confirmed
def profile():
    form = ChangePasswordForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(email=current_user.email).first()
        if user:
            user.password = bcrypt.generate_password_hash(form.password.data)
            db.session.commit()
            flash('Password successfully changed.', 'success')
            return redirect(url_for('user.profile'))
        else:
            flash('Password change was unsuccessful.', 'danger')
            return redirect(url_for('user.profile'))
    return render_template('users/profile.html', form=form)


@blueprint.route('/confirm/<token>')
@login_required
def confirm_email(token):
    if current_user.confirmed:
        flash('Account already confirmed. Please login.', 'success')
        return redirect(url_for('public.home'))
    email = confirm_token(token)
    user = User.query.filter_by(email=current_user.email).first_or_404()
    if user.email == email:
        user.confirmed = True
        user.confirmed_on = datetime.datetime.now()
        db.session.add(user)
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'success')
    else:
        flash('The confirmation link is invalid or has expired.', 'danger')
    return redirect(url_for('public.home'))


@blueprint.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.confirmed:
        return redirect(url_for('public.home'))
    flash('Please confirm your account!', 'warning')
    return render_template('users/unconfirmed.html')


@blueprint.route('/resend')
@login_required
def resend_confirmation():
    token = generate_confirmation_token(current_user.email)
    confirm_url = url_for('user.confirm_email', token=token, _external=True)
    html = render_template('users/activate.html', confirm_url=confirm_url)
    subject = "Please confirm your email"
    send_email(current_user.email, subject, html)
    flash('A new confirmation email has been sent.', 'success')
    return redirect(url_for('user.unconfirmed'))


@blueprint.route('/forgot',  methods=['GET', 'POST'])
def forgot():
    form = ForgotForm(request.form)
    if form.validate_on_submit():

        user = User.query.filter_by(email=form.email.data).first()
        token = generate_confirmation_token(user.email)

        user.password_reset_token = token
        db.session.commit()

        reset_url = url_for('user.forgot_new', token=token, _external=True)
        html = render_template('users/reset.html',
                               username=user.email,
                               reset_url=reset_url)
        subject = "Reset your password"
        send_email(user.email, subject, html)

        flash('A password reset email has been sent via email.', 'success')
        return redirect(url_for("public.home"))

    return render_template('users/forgot.html', form=form)


@blueprint.route('/forgot/new/<token>', methods=['GET', 'POST'])
def forgot_new(token):

    email = confirm_token(token)
    user = User.query.filter_by(email=email).first_or_404()

    if user.password_reset_token is not None:
        form = ChangePasswordForm(request.form)
        if form.validate_on_submit():
            user = User.query.filter_by(email=email).first()
            if user:
                user.password = bcrypt.generate_password_hash(form.password.data)
                user.password_reset_token = None
                db.session.commit()

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
