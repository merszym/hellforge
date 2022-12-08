from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@stringfilter
@register.filter(name='format')
def format(value, fmt):
    return fmt.format(value)