import datetime

from django import template
from django.conf import settings

from DSTBundesliga.apps.dstffbl.models import Announcement
from DSTBundesliga.apps.services import season_service
from DSTBundesliga.apps.services.state_service import StateService

register = template.Library()


@register.simple_tag
def get_announcements():
    return Announcement.objects.get_valid()


@register.simple_tag()
def is_registration_open():
    return season_service.is_registration_open()


@register.simple_tag()
def get_registration_starts():
    return settings.REGISTRATION_STARTS


@register.simple_tag()
def show_registration_countdown():
    return (
        datetime.date.fromisoformat(settings.REGISTRATION_STARTS)
        > datetime.date.today()
    )


@register.simple_tag()
def get_current_season():
    return StateService().get_season()
