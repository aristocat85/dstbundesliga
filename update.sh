#!/usr/bin/env bash
supervisorctl stop uwsgi
git pull
pip3.8 install -r requirements.txt --user
python3.8 manage.py migrate
python3.8 manage.py collectstatic --noinput
cp -r media/ ~/html/media/
supervisorctl start uwsgi
