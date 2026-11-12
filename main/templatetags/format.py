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
def text_color(background):
    """
    black or white text, whichever is more readable on the background (hex color), by the relative luminance (WCAG)
    """
    try:
        channels = [int(background.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    except (ValueError, AttributeError):
        return "black"
    r, g, b = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    # contrast with black (L + 0.05) / 0.05 vs. with white 1.05 / (L + 0.05)
    return "black" if (luminance + 0.05) / 0.05 >= 1.05 / (luminance + 0.05) else "white"


@register.filter
def count_char(value, char):
    return str(value).count(char)


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


@register.inclusion_tag("main/samples/sample-row-oob.html", takes_context=True)
def sample_row_oob(context, sample):
    """
    the updated row of the sample-table, swapped out-of-band (e.g. in the response of the sample-modal)
    """
    from main.tools.site import sample_row_context

    return sample_row_context(context["request"], sample)


@register.inclusion_tag("main/analyzed_samples/analyzedsample-rows-oob.html", takes_context=True)
def library_rows_oob(context, library):
    """
    the updated rows of the library-table, swapped out-of-band (in the response of the library-modal)
    """
    from main.tools.analyzed_samples import library_rows_context

    return library_rows_context(context["request"], library)
