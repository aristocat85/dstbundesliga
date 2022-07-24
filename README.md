Getting Started
===============

Install requirements:
```bash
poetry install
```

Create local configuration files
```bash
cp .env_example .env
cp local_settings_example.py local_settings.py
```

Perform Database Migrations
```bash
poetry run python manage.py migrate
```

Run Redis
```bash
docker run --name=redis --publish=6379:6379 --hostname=redis --restart=on-failure --detach redis:latest
```

Start Server
```bash
poetry run python manage.py runserver 127.0.0.1:8000
```

Create requirements.txt
```bash
poetry export -f requirements.txt --without-hashes -o /src/requirements.txt 
```

Create new migrations
```bash
poetry run python manage.py makemigrations
```


Testdata
========

Testdata is provided as a fixture:
```bash
poetry run python manage.py loaddata DSTBundesliga/apps/leagues/fixtures/Season2020Testdata.json
```
