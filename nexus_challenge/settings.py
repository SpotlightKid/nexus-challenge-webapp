# -*- coding: utf-8 -*-
"""Application configuration.

Most configuration is set via environment variables.

For local development, use a .env file to set environment variables.

"""

# Standard library modules
import datetime

# Third-party modules
from environs import Env


env = Env()
env.read_env()

ENV = env.str('FLASK_ENV', default='production')
DEBUG = ENV == 'development'
SQLALCHEMY_DATABASE_URI = env.str('DATABASE_URL')
SECRET_KEY = env.str('SECRET_KEY')
BCRYPT_LOG_ROUNDS = env.int('BCRYPT_LOG_ROUNDS', default=13)
DEBUG_TB_ENABLED = env.bool('DEBUG_TB_ENABLED', default=DEBUG)
DEBUG_TB_INTERCEPT_REDIRECTS = False
CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.
SQLALCHEMY_TRACK_MODIFICATIONS = False

SECURITY_PASSWORD_SALT = env.str('PASSWORD_SALT')
WTF_CSRF_ENABLED = True

# mail
MAIL_SERVER = env.str('APP_MAIL_SERVER', default='osamc.de')
MAIL_USE_TLS = env.bool('APP_MAIL_USE_TLS', default=False)
MAIL_USE_SSL = env.bool('APP_MAIL_USE_SSL', default=True)
MAIL_PORT = env.int('APP_MAIL_PORT', default=465 if MAIL_USE_SSL else 587)
MAIL_SUPPRESS_SEND = env.bool('MAIL_SUPPRESS_SEND', default=False)
MAIL_DEBUG = env.bool('MAIL_DEBUG', default=False)

MAIL_USERNAME = env.str('APP_MAIL_USERNAME')
MAIL_PASSWORD = env.str('APP_MAIL_PASSWORD')

MAIL_DEFAULT_SENDER = env.str('APP_MAIL_DEFAULT_SENDER', default='challenge@osamc.de')

SITE_AUTHOR = "Open Source Audio Meeting Cologne"
SITE_TITLE = "Open Source Music Nexus Challenge"
SITE_URL = "https://nexus-challenge.osamc.de/"
SITE_EMAIL = "challenge@osamc.de"
SITE_ADMIN_EMAIL = "chris@chrisarndt.de"
SITE_DESCRIPTION = "Let's make some awesome Open Source music!"
NAVIGATION_LINKS = (
    ("/", "The Challenge"),
    ("/rules/", "Rules"),
    ("/faq/", "FAQ"),
    #("/submit/", "Enter"),
    #("/vote/", "Voting"),
    ("/list/", "Entries"),
    ("/results/", "Results"),
    ("/prizes/", "Prizes"),
    #("/fmsynths/", "FM Synths"),
    ("mailto:challenge@osamc.de", "Contact"),
)
SOCIAL_BUTTONS_CODE = (
    'https://twitter.com/osamCologne',
)

# Competition parameters
MIN_TRACK_LENGTH = 60.0
MAX_TRACK_LENGTH = 300.0
SUBMISSION_PERIOD_START = datetime.datetime(2019, 9, 19, 0, 0, 0)
SUBMISSION_PERIOD_END = datetime.datetime(2019, 10, 19, 23, 59, 59)
VOTING_PERIOD_START = datetime.datetime(2019, 10, 20, 0, 0, 0)
VOTING_PERIOD_END = datetime.datetime(2019, 10, 27, 0, 0, 0)
