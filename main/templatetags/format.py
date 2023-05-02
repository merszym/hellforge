from django import template
from django.template.defaultfilters import stringfilter
from titlecase import titlecase

register = template.Library()


@stringfilter
@register.filter(name="format")
def format(value, fmt):
    if value:
        return fmt.format(value)
    else:
        return value


@stringfilter
@register.filter(name="title")
def title(value):
    return titlecase(value)


@register.filter
def lookup(dictionary, key):
    return dictionary.get(key, None)
