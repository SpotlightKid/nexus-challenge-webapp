# -*- coding: utf-8 -*-
"""Flask extensions instantiation.

Each extension is initialized in the app factory located in app.py.

"""

# Third-party modules
from flask_bcrypt import Bcrypt
from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_misaka import Misaka
from flask_pagedown import PageDown
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect


bcrypt = Bcrypt()
csrf_protect = CSRFProtect()
login_manager = LoginManager()
db = SQLAlchemy()
misaka = Misaka()
mail = Mail()
migrate = Migrate()
pagedown = PageDown()
cache = Cache()
debug_toolbar = DebugToolbarExtension()
