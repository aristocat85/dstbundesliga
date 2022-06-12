import datetime

from django.conf import settings


def is_registration_open():
    return datetime.date.fromisoformat(settings.REGISTRATION_STARTS) \
           < datetime.date.today() \
           <= datetime.date.fromisoformat(settings.REGISTRATION_STOPS)
