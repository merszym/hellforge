from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from main.models import Layer, Culture, Epoch, Checkpoint, Site
import statistics


def calculate_layer_dates(layer):
    """Calculate the layer date for DISPLAY in the overviews, use heuristics if no direct date is set"""
    # get direct date upper, lower
    if layer.date.first():
        upper = statistics.mean([x.upper for x in layer.date.all()])
    # get the lower bounds of underlying layer
    elif layer.get_lower_sibling():
        upper = layer.get_lower_sibling().mean_lower
    # or get the date of the assigned culture
    elif layer.culture:
        upper = layer.culture.upper
    else:
        upper = layer.mean_upper

    if layer.date.first():
        lower = statistics.mean([x.lower for x in layer.date.all()])
    # get the lower bounds of underlying layer
    elif layer.get_upper_sibling():
        lower = layer.get_upper_sibling().mean_upper
    # or get the date of the assigned culture
    elif layer.culture:
        lower = layer.culture.lower
    else:
        lower = layer.mean_lower
    return upper,lower



@receiver(post_save, sender=Layer)
def update_layer(sender, instance, **kwargs):
    """
    when layers are updated/saved, set the site for a direct link, update the dates
    """
    if not instance.site:
        instance.site = instance.profile.first().site
        instance.save()

    upper, lower = calculate_layer_dates(instance)
    print(instance, upper, lower)
    if (instance.mean_lower != lower) or (instance.mean_upper != upper):
        instance.mean_lower = lower
        instance.mean_upper = upper
        instance.save()


@receiver(post_save, sender=Layer)
def calc_culture_range(sender, instance, **kwargs):
    """
    When layers are updated/saved, set the upper and lower bounds of the associated cultures
    """
    culture = instance.culture
    if culture:
        dates = []
        for layer in Layer.objects.filter(culture=culture.pk):
            dates.extend(list(layer.date.all()))
        if len(dates) >= 1:
            culture.upper = max([x.upper for x in dates])
            culture.lower = min([x.lower for x in dates])
            culture.save()
