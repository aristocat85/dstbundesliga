import datetime

from django.conf import settings


def is_registration_open():
    print(datetime.date.fromisoformat(settings.REGISTRATION_STARTS))
    return datetime.date.fromisoformat(settings.REGISTRATION_STARTS) \
           < datetime.date.today() \
           <= datetime.date.fromisoformat(settings.REGISTRATION_STOPS)
