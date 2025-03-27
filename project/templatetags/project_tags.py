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

@register.simple_tag
def active_url(request, url_name):
    """Check if the current URL matches the given URL name"""
    if request.resolver_match and request.resolver_match.url_name == url_name:
        return "active"
    return ""
