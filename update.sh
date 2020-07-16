#!/usr/bin/env bash
supervisorctl stop uwsgi
git pull
python3.8 manage.py migrate
python3.8 manage.py collectstatic
supervisorctl start uwsgi
