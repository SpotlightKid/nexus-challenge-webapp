# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
from flask import Flask, render_template

from . import commands, public, user
from .extensions import (bcrypt, cache, csrf_protect, db, debug_toolbar, login_manager, mail,
                         migrate)


def _check_config_variables_are_set(config):
    assert config['MAIL_USERNAME'] is not None,\
           'MAIL_USERNAME is not set, set the env variable APP_MAIL_USERNAME '\
           'or MAIL_USERNAME in the production config file.'
    assert config['MAIL_PASSWORD'] is not None,\
           'MAIL_PASSWORD is not set, set the env variable APP_MAIL_PASSWORD '\
           'or MAIL_PASSWORD in the production config file.'

    assert config['SECRET_KEY'] is not None,\
           'SECRET_KEY is not set, set it in the production config file.'
    assert config['SECURITY_PASSWORD_SALT'] is not None,\
           'SECURITY_PASSWORD_SALT is not set, '\
           'set it in the production config file.'

    assert config['SQLALCHEMY_DATABASE_URI'] is not None,\
           'SQLALCHEMY_DATABASE_URI is not set, '\
           'set it in the production config file.'

    if config['ENV'] == 'production':
        assert config['STRIPE_SECRET_KEY'] is not None,\
               'STRIPE_SECRET_KEY is not set, '\
               'set it in the production config file.'
        assert config['STRIPE_PUBLISHABLE_KEY'] is not None,\
               'STRIPE_PUBLISHABLE_KEY is not set, '\
               'set it in the production config file.'


def create_app(config_object='fmchallengewebapp.settings'):
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__.split('.')[0])
    app.config.from_object(config_object)
    _check_config_variables_are_set(app.config)
    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_shellcontext(app)
    register_commands(app)
    return app


def register_extensions(app):
    """Register Flask extensions."""
    bcrypt.init_app(app)
    cache.init_app(app)
    db.init_app(app)
    csrf_protect.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    if debug_toolbar:
        debug_toolbar.init_app(app)
    return None


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(public.views.blueprint)
    app.register_blueprint(user.views.blueprint)
    return None


def register_errorhandlers(app):
    """Register error handlers."""
    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return render_template('{0}.html'.format(error_code)), error_code
    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_shellcontext(app):
    """Register shell context objects."""
    def shell_context():
        """Shell context objects."""
        return {
            'db': db,
            'User': user.models.User}

    app.shell_context_processor(shell_context)


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(commands.test)
    app.cli.add_command(commands.lint)
    app.cli.add_command(commands.clean)
    app.cli.add_command(commands.urls)
