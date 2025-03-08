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

@register.filter(name='is_recent_comment')
def is_recent_comment(value):
    """
    Check if a comment is less than 1 hour old.
    Usage: {{ comment.timestamp|is_recent_comment }}
    """
    if not value:
        return False
    now = datetime.now(value.tzinfo)
    diff = now - value
    return diff < timedelta(hours=1)