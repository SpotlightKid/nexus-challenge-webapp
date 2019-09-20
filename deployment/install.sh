#!/bin/bash
#
# install.sh - You must run this from the root of a repo checkout

mkdir -p "$HOME"/bin
mkdir -p "$HOME"/etc
mkdir -p "$HOME"/htdocs
mkdir -p "$HOME"/var/{db,log,run,backup}
install -m 640 deployment/nexus-challenge-webapp-prod.env "$HOME"/etc
install -m 755 deployment/start-nexus-challenge-webapp.sh "$HOME"/bin/start-nexus-challenge-webapp.sh
sudo install -m 644 deployment/nexus-challenge-webapp-nginx.conf /etc/nginx/nexus-challenge-webapp.conf
sudo install -m 644 deployment/nexus-challenge-webapp-supervisord.conf /etc/supervisord/conf.d/nexus-challenge-webapp.conf
ln -sf "$(pwd)"/nexus-challenge/static "$HOME"/htdocs

if [ -n "$VIRTUAL_ENV" ]
    pip install .
else
    echo "Activate the virtual environment for this app and run 'pip install .'"
fi
