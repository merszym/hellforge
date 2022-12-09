from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@stringfilter
@register.filter(name='format')
def format(value, fmt):
    if value:
        return fmt.format(value)
    else:
        return value