from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from main.models import Layer, Culture, Epoch, Checkpoint, Site
import statistics


def calculate_layer_dates(layer):
    """Calculate the layer date for DISPLAY in the overviews, use heuristics if no direct date is set"""
    upper_sibling = layer.get_upper_sibling()
    lower_sibling = layer.get_lower_sibling()
    upper = 100000
    lower = 0
    if layer.culture:
        upper = layer.culture.upper
        lower = layer.culture.lower
    if layer.epoch:
        epdate = layer.epoch.date.first()
        if upper > epdate.upper:
            upper = epdate.upper
        if lower < epdate.lower:
            lower = epdate.lower
    # checkpoints probably the most tricky... I keep that in for now
    # from here on, check, if the checkpoints/siblings are a more PRECISE date
    if layer.checkpoint.first():
        for cp in layer.checkpoint.all():
            cpdate = cp.date.first()
            if (cpdate.upper - cpdate.lower) < (upper-lower):
                if upper > cpdate.upper:
                    upper = cpdate.upper
                if lower < cpdate.lower:
                    lower = cpdate.lower
    # related dating is higher priority
    # unless the dates of the siblings are totally off...
    if upper_sibling:
        if lower_sibling:
            upper = statistics.mean([upper_sibling.mean_upper, lower_sibling.mean_upper])
            lower = statistics.mean([upper_sibling.mean_lower, lower_sibling.mean_lower])
        else:
            if (upper_sibling.mean_upper - upper_sibling.mean_lower) < (upper-lower):
                lower = upper_sibling.mean_upper
    if lower_sibling and not upper_sibling:
        if (lower_sibling.mean_upper - lower_sibling.mean_lower) < (upper-lower):
            upper = lower_sibling.mean_lower

    # get direct date upper, lower
    if layer.date.first():
        upper = statistics.mean([x.upper for x in layer.date.all()])
        lower = statistics.mean([x.lower for x in layer.date.all()])
    return upper,lower


@receiver(post_save, sender=Layer)
def update_layer(sender, instance, **kwargs):
    """
    when layers are updated/saved, set the site for a direct link, update the dates
    """
    if not instance.site:
        instance.site = instance.profile.first().site

    upper, lower = calculate_layer_dates(instance)
    if (instance.mean_lower != lower) or (instance.mean_upper != upper):
        instance.mean_lower = lower
        instance.mean_upper = upper
        instance.save()


@receiver(post_save, sender=Layer)
@receiver(post_save, sender=Culture)
def calc_culture_range(sender, instance, **kwargs):
    """
    When layers are updated/saved, set the upper and lower bounds of the associated cultures.
    Include the children-cultures!
    """
    try:
        culture = instance.culture
    except:
        culture = instance
    if culture:
        dates = []
        # if a culture was not directly dated...
        mean_lower = []
        mean_upper = []
        for cult in culture.all_cultures():
            for layer in Layer.objects.filter(culture=cult.pk):
                dates.extend(list(layer.date.all()))
                mean_lower.append(layer.mean_lower)
                mean_upper.append(layer.mean_upper)
        if len(dates) >= 1:
            upper = max([x.upper for x in dates])
            lower = min([x.lower for x in dates])
        elif len(mean_lower) >= 1:
            upper = max(mean_upper)
            lower = min(mean_lower)
        else:
            upper = 100000
            lower = 0
        if (culture.upper != upper) and (culture.lower != lower):
            culture.upper = upper
            culture.lower = lower
            culture.save()
