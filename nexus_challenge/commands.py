# -*- coding: utf-8 -*-
"""Click commands."""

# Standard library modules
import datetime
import os
import time
from email.utils import formataddr
from glob import glob as fglob
from operator import itemgetter
from os.path import abspath, exists, join
from subprocess import call

# Third-party modules
import click
from flask import current_app, render_template
from flask.cli import AppGroup, with_appcontext
from flask_mail import Message
from internetarchive import download as ia_download, get_item as ia_get_item
from werkzeug.exceptions import MethodNotAllowed, NotFound

from .competition.models import CompetitionEntry
from .database import db
from .extensions import mail
from .user.models import User
from .utils import canonify_track_url


HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.join(HERE, os.pardir)
TEST_PATH = os.path.join(PROJECT_ROOT, 'tests')


@click.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('pytest_args', nargs=-1, type=click.UNPROCESSED)
def test(pytest_args):
    """Run the tests."""
    import pytest
    rv = pytest.main([TEST_PATH] + list(pytest_args))
    exit(rv)


@click.command()
@click.option('-f', '--fix-imports', default=False, is_flag=True,
              help='Fix imports using isort, before linting')
def lint(fix_imports):
    """Lint and check code style with flake8 and isort."""
    def execute_tool(description, *args):
        """Execute a checking tool with its arguments."""
        command_line = list(args)
        click.echo('{}: {}'.format(description, ' '.join(command_line)))
        rv = call(command_line)
        if rv != 0:
            exit(rv)

    if fix_imports:
        execute_tool('Fixing import order', 'isort', '-rc', 'nexus_challenge', 'tests',
                     *fglob('*.py'))

    execute_tool('Checking code style', 'flake8')


@click.command()
def clean():
    """Remove *.pyc and *.pyo files recursively starting at current directory.

    Borrowed from Flask-Script, converted to use Click.
    """
    for dirpath, dirnames, filenames in os.walk('.'):
        for filename in filenames:
            if filename.endswith('.pyc') or filename.endswith('.pyo'):
                full_pathname = os.path.join(dirpath, filename)
                click.echo('Removing {}'.format(full_pathname))
                os.remove(full_pathname)


@click.command()
@click.option('--url', default=None,
              help='Url to test (ex. /static/image.png)')
@click.option('--order', default='rule',
              help='Property on Rule to order by (default: rule)')
@with_appcontext
def urls(url, order):
    """Display all of the url matching routes for the project.

    Borrowed from Flask-Script, converted to use Click.
    """
    rows = []
    column_length = 0
    column_headers = ('Rule', 'Endpoint', 'Arguments')

    if url:
        try:
            rule, arguments = (
                current_app.url_map
                           .bind('localhost')
                           .match(url, return_rule=True))
            rows.append((rule.rule, rule.endpoint, arguments))
            column_length = 3
        except (NotFound, MethodNotAllowed) as e:
            rows.append(('<{}>'.format(e), None, None))
            column_length = 1
    else:
        rules = sorted(
            current_app.url_map.iter_rules(),
            key=lambda rule: getattr(rule, order))
        for rule in rules:
            rows.append((rule.rule, rule.endpoint, None))
        column_length = 2

    str_template = ''
    table_width = 0

    if column_length >= 1:
        max_rule_length = max(len(r[0]) for r in rows)
        max_rule_length = max_rule_length if max_rule_length > 4 else 4
        str_template += '{:' + str(max_rule_length) + '}'
        table_width += max_rule_length

    if column_length >= 2:
        max_endpoint_length = max(len(str(r[1])) for r in rows)
        # max_endpoint_length = max(rows, key=len)
        max_endpoint_length = (
            max_endpoint_length if max_endpoint_length > 8 else 8)
        str_template += '  {:' + str(max_endpoint_length) + '}'
        table_width += 2 + max_endpoint_length

    if column_length >= 3:
        max_arguments_length = max(len(str(r[2])) for r in rows)
        max_arguments_length = (
            max_arguments_length if max_arguments_length > 9 else 9)
        str_template += '  {:' + str(max_arguments_length) + '}'
        table_width += 2 + max_arguments_length

    click.echo(str_template.format(*column_headers[:column_length]))
    click.echo('-' * table_width)

    for row in rows:
        click.echo(str_template.format(*row[:column_length]))


@click.command()
@with_appcontext
def create_db():
    """Creates the db tables."""
    db.create_all()


@click.command()
@with_appcontext
def drop_db():
    """Drops the db tables."""
    db.drop_all()


@click.command()
@click.option('--name', '-n', default='admin', prompt=True, help='Username for admin account')
@click.password_option()
@with_appcontext
def create_admin(name, password):
    """Creates the admin user."""
    user = User.query.filter_by(username=name).first()
    if user:
        if click.confirm("User '{}' already exists. Update password?".format(name)):
            user.update(password=password)
            click.echo('Password updated.')
        else:
            click.echo('User unchanged.')
    else:
        User.create(
            username=name,
            email='{}@example.com'.format(name),
            password=password,
            is_admin=True,
            is_active=True,
            is_confirmed=True,
            confirmed_on=datetime.datetime.now()
        )
        click.echo("User '{}' created.".format(name))


# Commands to handle send notification and reminder emails
email_group = AppGroup('email')


@email_group.command()
@click.option('--dry-run', '-n', default=False, is_flag=True,
              help='Do not sent actual email, just print it')
def publish_reminder(dry_run):
    """Send an email to users with unpublished competition entries."""
    entries = CompetitionEntry.query.filter_by(is_published=False)
    click.echo("Sending entry publication reminder to {} users.".format(entries.count()))

    with mail.record_messages() as outbox, current_app.test_request_context():
        for entry in entries:
            try:
                entry_url = "{}/submit/".format(current_app.config['SITE_URL'].rstrip('/'))
                body = render_template(
                    'competition/reminder_publish.html',
                    entry_url=entry_url,
                    entry=entry,
                    user=entry.user,
                    deadline=current_app.config['SUBMISSION_PERIOD_END']
                )
                subject = 'Reminder: your Nexus Challenge competition entry is still unpublished!'
                recipient = formataddr((entry.user.username, entry.user.email))
                msg = Message(
                    subject,
                    recipients=[recipient],
                    html=body,
                    sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
                )

                if dry_run:
                    click.echo("\nTo: {}\nSubject: {}\n\n{}\n".format(recipient, subject, body))
                else:
                    mail.send(msg)
            except Exception:
                current_app.logger.exception("Error sending entry publication reminder.")
                click.echo("Could not send entry publication reminder '{}'. "
                           "See log for details".format(recipient))
            else:
                click.echo("Entry publication reminder sent to '{}'.".format(recipient))

    click.echo("\nAll done. {} emails sent.".format(len(outbox)))


@email_group.command()
@click.option('--dry-run', '-n', default=False, is_flag=True,
              help='Do not sent actual email, just print it')
@click.option('--entry-id', '-e', type=int,
              help='Send reminder only to user who submitted entry with given id')
def voting_reminder(dry_run=False, entry_id=None):
    """Send an email to users who published a competition entry, reminding them to vote."""
    if entry_id:
        entries = CompetitionEntry.query.filter_by(id=entry_id)
    else:
        entries = CompetitionEntry.query.filter_by(is_approved=True)

    click.echo("Sending entry voting reminder to {} users.".format(entries.count()))

    with mail.record_messages() as outbox, current_app.test_request_context():
        for entry in entries:
            try:
                entry_url = "{}/vote/".format(current_app.config['SITE_URL'].rstrip('/'))
                body = render_template(
                    'competition/reminder_voting.html',
                    entry_url=entry_url,
                    entry=entry,
                    user=entry.user,
                )
                subject = 'Reminder: your vote is needed in the Nexus Challenge!'
                recipient = formataddr((entry.user.username, entry.user.email))
                msg = Message(
                    subject,
                    recipients=[recipient],
                    html=body,
                    sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
                )

                if dry_run:
                    click.echo("\nTo: {}\nSubject: {}\n\n{}\n".format(recipient, subject, body))
                else:
                    mail.send(msg)
            except Exception:
                current_app.logger.exception("Error sending voting reminder.")
                click.echo("Could not send voting reminder '{}'. "
                           "See log for details".format(recipient))
            else:
                click.echo("Entry voting reminder sent to '{}'.".format(recipient))

    click.echo("\nAll done. {} emails sent.".format(len(outbox)))


# Commands to handle competition maintenance tasks
compo_group = AppGroup('compo')


@compo_group.command()
def check_votes():
    """Display list of competition entries and whether the user, who submitted it, has voted."""
    for entry in CompetitionEntry.query.filter_by(is_approved=True).order_by('title'):
        click.echo("{e.artist} - {e.title}".format(e=entry))
        click.echo("User: {}".format(entry.user.username))
        click.echo("Voted: {}".format("yes" if bool(entry.user.votes) else "no"))
        click.echo('')


@click.option('--anonymize', '-a', default=False, is_flag=True,
              help='Do not reveal artist or song name, just fake names')
@compo_group.command()
def print_scoreboard(anonymize=False):
    """Print list of entries with total score."""
    results = []

    for entry in CompetitionEntry.query.filter_by(is_approved=True):
        points = sum(vote.points for vote in entry.votes)
        results.append((points, entry))

    for i, (points, entry) in enumerate(sorted(results, key=itemgetter(0), reverse=True)):
        if anonymize:
            click.echo("artist #{i} - <hidden title>: {p}".format(i=i, p=points))
        else:
            click.echo("{e.artist} - {e.title}: {p}".format(e=entry, p=points))


@click.option('--dry-run', '-n', default=False, is_flag=True,
              help='Do not actually download anything, just print what would be downloaded')
@click.option('--entry-id', '-e', type=int,
              help='Download only file of entry with given id')
@click.option('--glob', '-g',
              help='Restrict downloaded files to those matching given glob pattern')
@click.argument('output_dir')
@compo_group.command()
def download_entries(output_dir, dry_run=False, entry_id=None, glob=None):
    """Download all files of all or competition entries or of one entry."""
    if entry_id:
        entries = CompetitionEntry.query.filter_by(id=entry_id)
    else:
        entries = CompetitionEntry.query.filter_by(is_approved=True)

    try:
        if not exists(output_dir):
            os.makedirs(output_dir)
        os.chdir(output_dir)

        for entry in entries:
            url, track_id = canonify_track_url(entry.url)

            destdir = abspath(join(output_dir, track_id))
            click.echo("Downloading files for item '{}' to directory '{}'...".format(
                       track_id, destdir))

            if dry_run:
                try:
                    item = ia_get_item(track_id, request_kwargs={'timeout': 30})
                    metadata = item.item_metadata.get('metadata')
                    if not metadata:
                        raise ValueError("'%s' not found." % track_id)
                except Exception as exc:
                    click.echo("Could not get meta data for item '{}' from Archive.org: {}".format(
                               track_id, exc))
                else:
                        for file in item.files:
                            click.echo("'{}' size: {:3.2f} kB...".format(
                                       file['name'], int(file.get('size', 0)) / 1024))
            else:
                try:
                    ia_download(track_id, glob_pattern=glob, verbose=True,
                                formats=['FLAC', 'Metadata'])
                except Exception as exc:
                    click.echo("Error downloading item '{}' from Archive.org: {}".format(
                               track_id, exc))
                # be nice (server drops connection frequently otherwise)
                time.sleep(1.0)

    except KeyboardInterrupt:
        click.echo("Aborted.")


def label_barh(ax, fmt="{}", spacing=5, align='left', is_inside=False, **kwargs):
    """Attach a text label to each horizontal bar displaying its y value.

    fmt     - Format string for labels or callable with receives a value and gives
              it back formatted as a string.
    spacing - Number of points between bar and label (default: 5).
    align   - Alignment for positive values.


    """
    for rect in ax.patches:
        # Get X and Y placement of label from rect.
        x_value = rect.get_width()
        y_value = rect.get_y() + rect.get_height() / 2

        # Use X value as label and format number accodring to given fmt (function)
        if callable(fmt):
            label = fmt(x_value)
        else:
            label = fmt.format(x_value)

        # If value of bar is negative: Place label left of bar
        if x_value < 0 or is_inside:
            # Invert space to place label to the left
            spacing *= -1
            # Horizontally align label at right
            align = 'right'

        # Create annotation
        ax.annotate(
            label,                          # Use `label` as label
            (x_value, y_value),             # Place label at end of the bar
            xytext=(spacing, 0),            # Horizontally shift label by `spacing`
            textcoords="offset points",     # Interpret `xytext` as offset in points
            va='center',                    # Vertically center label
            ha=align,                       # Horizontally align label according to sign
            **kwargs)


def ellip(s, maxlen=25, suffix="…"):
    """Truncate string to maxlen if neccessary.

    If string is truncated, suffix it with suffix, whose length is included in maxlen.

    """
    if len(s) < maxlen:
        return s
    else:
        return s[:maxlen - len(suffix)] + suffix


@click.option('--output', '-o', help='Save figure to given file name.')
@click.option('--toolkit', '-t', default='Qt5Agg',
              help="Toolkit matplotlib shoud use (default: 'Qt5Agg').")
@compo_group.command()
def scoregraph(output, toolkit):
    """Generate a horizontal bar graph showing the total score of each track."""
    import matplotlib
    matplotlib.use(toolkit)
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd

    # Accumulate data
    entries = []
    for entry in CompetitionEntry.query.filter_by(is_approved=True):
        data = {
            'title': "{title}\nby {artist}".format(artist=ellip(entry.artist),
                                                   title=ellip(entry.title)),
            'Total score': sum(vote.points for vote in entry.votes),
            '# of 5 point votes': sum(1 for vote in entry.votes if vote.points == 5),
            '# of 4 point votes': sum(1 for vote in entry.votes if vote.points == 4),
        }
        entries.append(data)

    entries.sort(key=itemgetter('Total score', '# of 5 point votes', '# of 5 point votes'),
                 reverse=False)
    entries_df = pd.DataFrame(entries)

    # build graph
    sns.set(style="whitegrid")

    # Plot the total score for each entry
    sns.set_color_codes("pastel")
    ax = entries_df.plot(kind='barh', figsize=(20, 10))
    ax.set_yticklabels(e['title'] for e in entries)

    label_barh(ax, lambda x: "{:d}".format(int(x)), color="dimgrey", fontsize="small")

    # Add a legend and informative axis label
    ax.legend(ncol=2, loc="lower right", frameon=True)
    ax.set(ylabel="", xlabel="Points")
    ax.set_title("Total score per competition entry", fontsize='x-large')

    sns.despine(left=True, bottom=True)

    if output:
        plt.savefig(output)
        click.echo("Figure saved as '{}'.".format(output))
    else:
        plt.show()



@click.option('--exclude', '-e', help='Comma separated list of usernames to exclude.')
@compo_group.command()
def raffle(exclude):
    """Select a random voter as the winner of the raffle."""
    import random

    if isinstance(exclude, str):
        exclude = set(username.strip() for username in exclude.split(','))
    elif exclude is None:
        exclude = set()

    # collect elegible users
    usernames = []
    for user in User.query.filter_by(is_confirmed=True):
        if user.votes and user.username not in exclude:
            usernames.append(user.username)

    click.echo("Selecting raffle winner from {:d} elegible voters...\n".format(len(usernames)))

    # just for good measure :)
    random.shuffle(usernames)

    # do the draw
    winner = random.choice(usernames)

    click.echo("The winner of the raffle is:\n\n*** {} ***\n".format(winner))
