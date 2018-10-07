#!/bin/bash

VENV="${VENV:-fmchallenge}"
VENV_ROOT="$HOME/.pyenv/versions/$VENV"

if [ -r "$HOME/etc/fmchallenge-webapp-prod.env" ]; then
    source "$HOME/etc/fmchallenge-webapp-prod.env"
else
    echo "Could not find production environment file." >/dev/stderr
    exit 1
fi

if [ -n "$VENV" -a -d "$VENV_ROOT" ]; then
    exec "$VENV_ROOT/bin/gunicorn" \
        -b 127.0.0.1:8088 \
        --reuse-port \
        -p "$HOME/var/run/fmchallenge-webapp.pid" \
        --access-logfile "$HOME/var/log/fmchallenge-webapp-access.log" \
        --error-logfile "$HOME/var/log/fmchallenge-webapp-error.log" \
        fmchallengewebapp.app:create_app\(\)
else
    echo "Virtual environment $VENV not found." >/dev/stderr
fi
