Getting Started
===============

Install requirements:
```bash
pip install -r requirements.txt
```

Create local configuration files
```bash
cp .env_example .env
cp local_settings_example.py local_settings.py
```

Perform Database Migrations
```bash
python manage.py migrate
```

Start Server
```bash
python manage.py runserver 127.0.0.1:8000
```


Testdata
========

Testdata is provided as a fixture:
```
python manage.py loaddata DSTBundesliga/apps/leagues/fixtures/Season2020Testdata.json
```
