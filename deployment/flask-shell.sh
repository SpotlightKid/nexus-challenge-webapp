#!/bin/bash

VENV="${VENV:-nexus-challenge37}"

cd "$HOME"/src/nexus-challenge-webapp
export FLASK_APP=autoapp.py
source "$HOME"/etc/nexus-challenge-webapp-prod.env
exec "$HOME"/.pyenv/versions/$VENV/bin/flask shell
