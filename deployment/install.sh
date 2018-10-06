#!/bin/bash
#
# install.sh - You must run this from the root of a repo checkout

mkdir -p "$HOME"/bin
mkdir -p "$HOME"/etc
mkdir -p "$HOME"/htdocs
mkdir -p "$HOME"/var/{db,log,run,backup}
install -m 640 deployment/fmchallenge-webapp-prod.env "$HOME"/etc
install -m 755 deployment/start-fmchallenge-webapp.sh "$HOME"/bin/start-fmchallenge-webapp.sh
sudo install -m 644 deployment/fmchallenge-webapp-nginx.conf /etc/nginx/fmchallenge-webapp.conf
sudo install -m 644 deployment/fmchallenge-webapp-supervisord.conf /etc/supervisord/conf.d/fmchallenge-webapp.conf
ln -sf "$(pwd)"/fmchallenge/static "$HOME"/htdocs

if [ -n "$VIRTUAL_ENV" ]
    pip install .
else
    echo "Activate the virtual environment for this app and run 'pip install .'"
fi
