from django import template
from django.conf import settings

register = template.Library()


@register.filter
def modulo(num, val):
    return num % val


@register.filter
def times(number):
    return range(number)

# settings value
@register.simple_tag
def settings_value(name):
    return getattr(settings, name, "")


@register.tag
def render_award(award, token):
    return award
