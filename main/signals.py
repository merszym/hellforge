from django.db.models.signals import post_save, m2m_changed, post_delete
from django.dispatch import receiver
from main.models import Layer, Culture, Site, Date, Project, Description
from main.tools import dating
import statistics
import json


def calculate_layer_dates(layer):
    """Calculate the layer date for DISPLAY in the overviews, use heuristics if no direct date is set"""
    upper = layer.mean_upper
    lower = layer.mean_lower
    if layer.date.first():
        all_upper = [x.upper for x in layer.date.all() if x.upper]
        all_lower = [x.lower for x in layer.date.all() if x.lower]

        # for dates that have only the lower value reported (>40000), add the date to the upper array as well
        all_upper.extend([x.lower for x in layer.date.all() if x.upper == None])

        if len(all_upper) > 0:
            upper = statistics.mean(all_upper)
        if len(all_lower) > 0:
            lower = statistics.mean(all_lower)
    # make sure lower is older than upper
    # with dates beyond radiocarbon, this might happen (because only lower is reported)
    if lower > upper:
        upper = lower
    layer.mean_lower = lower
    layer.mean_upper = upper

    layer.save()
    return layer


# after deleting or adding a date from the layer - save the layer to update the upper and lower
@receiver(m2m_changed, sender=Layer.date.through)
def update_dates(sender, instance, **kwargs):
    layer = calculate_layer_dates(instance)


# Date validation
@receiver(post_save, sender=Date)
def fill_date(sender, instance, **kwargs):
    if instance.method == "14C":
        if not instance.upper or not instance.raw:  # uncalibrated date
            if (
                instance.estimate and instance.plusminus
            ):  # some legacy dates dont have that?
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
        if instance.estimate and not instance.upper:  # instance.upper is recursion save
            if instance.plusminus:
                instance.upper = instance.estimate + instance.plusminus
                instance.lower = instance.estimate - instance.plusminus
                instance.save()


@receiver(post_save, sender=Layer)
def update_layer(sender, instance, **kwargs):
    """
    when layers are updated/saved, set the site for a direct link
    """
    if not instance.site:
        instance.site = instance.profile.first().site
        instance.save()


# calculate culture ranges
@receiver(post_save, sender=Culture)
def calc_culture_range(sender, instance, **kwargs):
    """
    When layers are updated/saved, set the upper and lower bounds of the associated cultures.
    Include the children-cultures!
    """
    culture = instance
    if culture:
        mean_lower = []
        mean_upper = []
        for cult in culture.all_cultures():
            for layer in Layer.objects.filter(culture=cult.pk):
                if layer.set_upper:
                    mean_upper.append(layer.set_upper)
                elif layer.mean_upper:
                    mean_upper.append(layer.mean_upper)
                if layer.set_lower:
                    mean_lower.append(layer.set_lower)
                elif layer.mean_lower:
                    mean_lower.append(layer.mean_lower)

        if len(mean_lower) >= 1:
            lower = statistics.median(mean_lower)
        if len(mean_upper) >= 1:
            upper = statistics.median(mean_upper)
        else:
            upper = None
            lower = None
        if culture.upper != upper and culture.lower != lower:
            # this is for recursion
            culture.upper = upper
            culture.lower = lower
            culture.save()


# after adding a site to a project - add a description if it doesnt yet exist
@receiver(m2m_changed, sender=Project.site.through)
def create_description(sender, instance, **kwargs):
    pk = set(kwargs.get("pk_set")).pop()
    site = kwargs.get("model").objects.get(pk=pk)
    # site = site
    # instance = the project
    if kwargs.pop("action", False) == "post_add":
        # filter all descriptions for site and project
        queryset = Description.objects.filter(site=site, project=instance)
        # if it doesnt exist: create one!
        if len(queryset) == 0:
            tmp = Description()
            tmp.save()
            tmp.refresh_from_db()
            tmp.project.add(instance)
            site.description.add(tmp)
