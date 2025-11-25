import os
from django import template

register = template.Library()

@register.filter
def basename(value):
    """Return the base filename from a path."""
    return os.path.basename(value) if value else ''
