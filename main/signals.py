from django.db.models.signals import post_save, m2m_changed, post_delete
from django.dispatch import receiver
from main.models import Layer, Culture, Epoch, Checkpoint, Site, Date, CheckpointLayerJunction
from main.tools import dating
import statistics
import json

def calculate_layer_dates(layer):
    """Calculate the layer date for DISPLAY in the overviews, use heuristics if no direct date is set"""
    upper_sibling = layer.get_upper_sibling()
    lower_sibling = layer.get_lower_sibling()
    upper = 100000
    lower = 0
    if layer.culture:
        #get the median of upper and lower dates of the given culture
        dates = []
        for cult in layer.culture.all_cultures():
            for lay in Layer.objects.filter(culture=cult.pk):
                dates.extend(list(lay.date.all()))
        if len(dates)>0:
            cupper = statistics.median([x.upper if x.upper else int(x.lower*2) for x in dates])
            clower = statistics.median([x.lower if x.lower else int(x.lower/2) for x in dates])
            if cupper:
                upper = cupper
            if clower:
                lower = clower
            if int(upper) < int(lower):
                upper,lower = lower,upper
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
            if upper_sibling.mean_upper and lower_sibling.mean_upper:
                upper = statistics.mean([upper_sibling.mean_upper, lower_sibling.mean_upper])
            if upper_sibling.mean_lower and lower_sibling.mean_lower:
                lower = statistics.mean([upper_sibling.mean_lower,lower_sibling.mean_lower])
        else:
            if (upper_sibling.mean_upper - upper_sibling.mean_lower) < (upper-lower):
                lower = upper_sibling.mean_upper
    if lower_sibling and not upper_sibling:
        if (lower_sibling.mean_upper - lower_sibling.mean_lower) < (upper-lower):
            upper = lower_sibling.mean_lower
    #sometimes context dates are just weird
    if lower > upper:
        lower = upper
    # get direct date upper, lower
    if layer.date.first():
        # check for dates that contain only one of upper or lower
        # ugly intermediate fix: >30k sets upper to 60k and <30k sets lower to 15k
        all_upper = [x.upper if x.upper else int(x.lower*2) for x in layer.date.all()]
        all_lower = [x.lower if x.lower else int(x.lower/2) for x in layer.date.all()]
        if len(all_upper) > 0:
            upper = statistics.mean(all_upper)
        if len(all_lower) > 0:
            lower = statistics.mean(all_lower)
    return upper,lower

#after deleting a date from the layer - save the layer to update the upper and lower
@receiver(m2m_changed, sender=Layer.date.through)
def update_dates(sender, instance, **kwargs):
    if kwargs.pop('action', False) == 'post_remove':
        instance.save()

# Date validation
@receiver(post_save, sender=Date)
def fill_date(sender, instance, **kwargs):
    if instance.method == '14C':
        if not instance.upper or not instance.raw: #uncalibrated date
            if instance.estimate and instance.plusminus: # some legacy dates dont have that?
                est = int(instance.estimate)
                pm = int(instance.plusminus)
                raw, upper, lower, curve = dating.calibrate(est, pm)
                if raw:
                    instance.upper = upper
                    instance.lower = lower
                    instance.curve = curve
                    instance.raw = json.dumps(raw)
                    instance.save()
    else:
        if instance.estimate and not instance.upper: #instance.upper is recursion save
            if instance.plusminus:
                instance.upper = instance.estimate + instance.plusminus
                instance.lower = instance.estimate - instance.plusminus
                instance.save()

@receiver(post_save, sender=Layer)
def update_layer(sender, instance, **kwargs):
    """
    when layers are updated/saved, set the site for a direct link, update the dates
    if no junction exists: save an additional junction
    """
    if not instance.site:
        instance.site = instance.profile.first().site
        instance.save()

    if len(instance.junction.all())==0:
        j = CheckpointLayerJunction(layer=instance)
        j.save()

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
            cupper = statistics.median([x.upper if x.upper else int(x.lower*2) for x in dates])
            clower = statistics.median([x.lower if x.lower else int(x.lower/2) for x in dates])
            if cupper:
                upper = cupper
            if clower:
                lower = clower
        elif len(mean_lower) >= 1:
            upper = max(mean_upper)
            lower = min(mean_lower)
        else:
            upper = 100000
            lower = 0
        if (culture.upper != upper) or (culture.lower != lower):
            culture.upper = upper
            culture.lower = lower
            culture.save()

@receiver(post_save, sender=Checkpoint)
def update_checkpoint(sender, instance, **kwargs):
    """
    if no junction exists: save an additional junction
    """
    if len(instance.junction.all())==0:
        j = CheckpointLayerJunction(checkpoint=instance)
        j.save()