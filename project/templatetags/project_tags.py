from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.filter
def jsonify(obj):
    """Convert a Python object into JSON string for JavaScript use"""
    if isinstance(obj, dict):
        return mark_safe(json.dumps(obj))
    return '{}'

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using the key"""
    return dictionary.get(key)


@register.filter
def split(value, sep=None):
    """Split a string by the given separator and return a list.

    Usage in template: {{ "a,b,c"|split:"," }}
    If value is None, returns an empty list. Strips whitespace from items.
    """
    if value is None:
        return []
    try:
        # ensure it's a string
        s = str(value)
        if sep is None:
            # default Python split behaviour
            parts = s.split()
        else:
            parts = s.split(sep)
        return [p.strip() for p in parts]
    except Exception:
        return []

@register.simple_tag
def active_url(request, url_name):
    """Check if the current URL matches the given URL name"""
    if request.resolver_match and request.resolver_match.url_name == url_name:
        return "active"
    return ""
