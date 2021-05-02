import datetime
from django import template

from DSTBundesliga.apps.dstffbl.models import Announcement

register = template.Library()


@register.simple_tag
def get_announcements():
    return Announcement.objects.get_valid()


