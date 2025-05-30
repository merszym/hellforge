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
    if dictionary:
        return dictionary.get(key, None)
    return None


@register.filter
def isin(key, collection):
    return key in collection


@register.filter(name="getstring")
def getstring(dict):
    try:
        return "&".join([f"{k}={v}" for k, v in dict.items()])
    except AttributeError: #if you render_to _string, dict becomes a string
        return ""


@register.filter(name="species_from_faunastring")
def species_from_faunastring(string):
    return string.split("__")[1]
