#!/bin/bash

VENV="${VENV:-nexus-challenge}"
VENV_ROOT="$HOME/.pyenv/versions/$VENV"

if [ -r "$HOME/etc/nexus-challenge-webapp-prod.env" ]; then
    source "$HOME/etc/nexus-challenge-webapp-prod.env"
else
    echo "Could not find production environment file." >/dev/stderr
    exit 1
fi

if [ -n "$VENV" -a -d "$VENV_ROOT" ]; then
    exec "$VENV_ROOT/bin/gunicorn" \
        -b 127.0.0.1:8088 \
        --reuse-port \
        -p "$HOME/var/run/nexus-challenge-webapp.pid" \
        --access-logfile "$HOME/var/log/nexus-challenge-webapp-access.log" \
        --error-logfile "$HOME/var/log/nexus-challenge-webapp-error.log" \
        nexus_challenge.app:create_app\(\)
else
    echo "Virtual environment $VENV not found." >/dev/stderr
fi
