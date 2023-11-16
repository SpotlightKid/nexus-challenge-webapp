# -*- coding: utf-8 -*-
"""Flask extensions instantiation.

Each extension is initialized in the app factory located in app.py.

"""

# Third-party modules
from flask_bcrypt import Bcrypt
from flask_caching import Cache
#from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_pagedown import PageDown
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from .ext.flask_misaka import Misaka

bcrypt = Bcrypt()
cache = Cache()
csrf_protect = CSRFProtect()
db = SQLAlchemy()
#debug_toolbar = DebugToolbarExtension()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
misaka = Misaka()
pagedown = PageDown()
