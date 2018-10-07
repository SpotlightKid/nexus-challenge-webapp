#!/bin/bash

VENV="${VENV:-fmchallenge37}"

cd "$HOME"/src/fmchallenge-webapp
export FLASK_APP=autoapp.py
source "$HOME"/etc/fmchallenge-webapp-prod.env
exec "$HOME"/.pyenv/versions/$VENV/bin/flask shell
