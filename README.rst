===============================
Nexus Challenge Web App
===============================

Dynamic web site for the Open Source Music Nexus Challenge


Quickstart
----------

Run the following commands to bootstrap your environment ::

    git clone https://github.com/SpotlightKid/nexus-challenge-webapp
    cd nexus-challenge-webapp
    pip install -r requirements/dev.txt
    cp env.example .env

Then edit `.env` to set the database URI and the mail configuration.

Once you have installed your DBMS, run the following to create your app's
database tables and perform the initial migration ::

    flask db init
    flask db migrate
    flask db upgrade

Then start the flask development server:

    flask run

Go to http://127.0.0.1:5000/ and you will (hopefully) see a pretty welcome
screen.


Deployment
----------

To deploy::

    export FLASK_ENV=production
    export FLASK_DEBUG=0
    export DATABASE_URL="<YOUR DATABASE URL>"
    flask run       # start the flask server

In your production environment, make sure the ``FLASK_DEBUG`` environment
variable is unset or is set to ``0``.


Shell
-----

To open the interactive shell, run ::

    flask shell

By default, you will have access to the flask ``app``.


Running Tests
-------------

To run all tests, run ::

    flask test


Migrations
----------

Whenever a database migration needs to be made. Run the following commands ::

    flask db migrate

This will generate a new migration script. Then run ::

    flask db upgrade

To apply the migration.

For a full migration command reference, run ``flask db --help``.
