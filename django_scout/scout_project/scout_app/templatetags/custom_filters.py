from django import template
from django.utils.timesince import timesince
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def custom_timesince(value):
    now = datetime.now(value.tzinfo)
    diff = now - value
    if diff >= timedelta(hours=1):
        hours = diff.seconds // 3600
        return f"{hours}h"
    else:
        minutes = diff.seconds // 60
        return f"{minutes}m"