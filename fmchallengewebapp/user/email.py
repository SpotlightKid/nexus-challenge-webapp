# project/email.py

from flask_mail import Message

from flask import current_app
from ..extensions import mail


def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
    )
    mail.send(msg)
