# -*- coding: utf-8 -*-
"""User blueprint email helper module."""

from flask import current_app
from flask_mail import Message

from fmchallengewebapp.extensions import mail


def send_email(recipient, subject, template):
    """Send email to recipient with subject using template."""
    msg = Message(
        subject,
        recipients=[recipient],
        html=template,
        sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
    )
    mail.send(msg)
