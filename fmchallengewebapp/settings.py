# -*- coding: utf-8 -*-
"""Application configuration.

Most configuration is set via environment variables.

For local development, use a .env file to set environment variables.

"""

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

MAIL_USERNAME = env.str('APP_MAIL_USERNAME')
MAIL_PASSWORD = env.str('APP_MAIL_PASSWORD')

MAIL_DEFAULT_SENDER = env.str('APP_MAIL_DEFAULT_SENDER', default='fmchallenge@osamc.de')

SITE_AUTHOR = "Open Source Audio Meeting Cologne"
SITE_TITLE = "Open Source Music FM Synthesizer Challenge"
SITE_URL = "https://fmchallenge.osamc.de/"
SITE_EMAIL = "fmchallenge@osamc.de"
SITE_DESCRIPTION = "Let's create awesome music with Open Source FM Synthesizers!"
NAVIGATION_LINKS = (
    ("/", "The Challenge"),
    ("/rules/", "Rules"),
    ("/submit/", "Enter"),
    ("/vote/", "Voting"),
    ("/fmsynths/", "FM Synths"),
    ("mailto:fmchallenge@osamc.de", "Contact"),
    #("/blog/", "Blog"),
    #("/rss.xml", "RSS feed"),
)
SOCIAL_BUTTONS_CODE = (
    'https://twitter.com/osamCologne',
)

# Competition parameters
MIN_TRACK_LENGTH = 60.0
MAX_TRACK_LENGTH = 300.0
