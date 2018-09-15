# -*- coding: utf-8 -*-
"""User blueprint email helper module."""

from multiprocessing import get_context

from flask import current_app
from flask_mail import Message

from fmchallengewebapp.extensions import mail


def send_email(app, recipient, subject, template):
    """Send email to recipient with subject using template."""
    with app.app_context():
        msg = Message(
            subject,
            recipients=[recipient],
            html=template,
            sender=app.config.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
        )
        try:
            mail.send(msg)
        except Exception:
            app.logger.exception("Failed to send email with subject '%s' to '%s'.",
                                 subject, recipient)


def start_send_email_task(recipient, subject, template):
    ctx = get_context('fork')
    proc = ctx.Process(target=send_email, args=(current_app, recipient, subject, template),
                       daemon=True)
    proc.start()
