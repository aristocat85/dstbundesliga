#!/usr/bin/env bash
supervisorctl stop uwsgi
git pull
poetry export -f requirements.txt --output requirements.txt
pip3.8 install -r requirements.txt --user --upgrade
python3.8 manage.py migrate
python3.8 manage.py collectstatic --noinput
cp -rf media/* ~/html/media/
supervisorctl start uwsgi

