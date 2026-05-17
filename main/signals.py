import numpy
from django.db.models.signals import pre_save, post_save, m2m_changed, post_delete
from django.dispatch import receiver
from main.models import (
    Layer,
    Culture,
    Site,
    Date,
    Project,
    Description,
    Sample,
    FaunalResults,
    Reference,
    SampleBatch,
    Gallery,
    ColourName,
    ColourMunsell
)
from main.tools import dating
import json
import statistics
from django.templatetags.static import static
import re
import colour


# after deleting or adding a date from a dateable - update the mean_upper and mean_lower
@receiver(m2m_changed, sender=Sample.date.through)
@receiver(m2m_changed, sender=Layer.date.through)
def update_dates(sender, instance, **kwargs):
    if kwargs.pop("action", False) in ["post_add", "post_remove"]:
        dating.recalculate_mean(instance)


# Get BibTex from DOI and render the HTML citation
@receiver(post_save, sender=Reference)
def get_bibtex_and_render_citation(sender, instance, **kwargs):
    from main.tools.references import doi2bib, bibtex_replace_key, render_single_citation
    if instance.doi.startswith("10") and not instance.bibtex:
        bibtex = doi2bib(instance.doi, instance.pk)
        html, short = render_single_citation(bibtex)
        instance.bibtex = bibtex
        instance.parsedHTML = html
        instance.parsedInline = short
        instance.save()
    if instance.bibtex and not re.search(r"\{(reference_[0-9]+)",instance.bibtex):
        bibtex = bibtex_replace_key(instance.bibtex, instance.pk)
        instance.bibtex = bibtex
        html, short = render_single_citation(bibtex)
        instance.parsedHTML = html
        instance.parsedInline = short
        instance.save()
    if instance.bibtex and not instance.parsedHTML:
        html, short = render_single_citation(instance.bibtex)
        instance.parsedHTML = html
        instance.parsedInline = short
        instance.save()


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
                    instance.sigma = "95%"
                    instance.save()
    else:
        try:
            if instance.sigma.endswith("s"):
                instance.sigma = instance.sigma.replace(
                    "s", "σ"
                )  # replace s with sigma, because this is how I want it to be
                instance.save()
        except AttributeError:
            pass
        if (instance.estimate and instance.plusminus and not instance.upper) or (
            instance.sigma == "1σ" and instance.plusminus
        ):  # instance.upper is recursion save
            # We want all the non-14C dates to be shown as 2σ values
            # That means, that we have to *double* the plusminus if only 1σ is provided (we can because sigma means normaly distributed)
            if instance.sigma == "1σ":
                if instance.plusminus:
                    instance.plusminus = instance.plusminus * 2
                    instance.sigma = "2σ"

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
    upper = None
    lower = None

    culture = instance
    query = culture.all_cultures()

    uppers = []
    lowers = []

    for layer in Layer.objects.filter(culture__in=query):
        infinite, tmp_upper, tmp_lower = layer.get_upper_and_lower(calculate_mean=True)

        uppers.append(tmp_upper)
        lowers.append(tmp_lower)

    uppers = [x for x in uppers if x != None]
    lowers = [x for x in lowers if x != None]

    if len(lowers) >= 1:
        lower = statistics.mean(lowers)
    if len(uppers) >= 1:
        upper = statistics.mean(uppers)

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


@receiver(post_save, sender=SampleBatch)
def create_gallery(sender, instance, created, **kwargs):
    batch = instance
    # Create a Gallery for each Batch
    if created and not batch.gallery:
        gallery = Gallery.objects.create(title=batch.name)
        SampleBatch.objects.filter(pk=batch.pk).update(gallery=gallery)

# after saving a faunalResults, update the order! (I assume that in most cases I dont do that...)
@receiver(post_save, sender=FaunalResults)
def update_order(sender, instance, **kwargs):
    from main.models import Taxonomy

    if instance.order != instance.order:
        # this is because the order is set to a np.nan instance...

        try:
            t = Taxonomy.objects.get(type="family_order")
            data = json.loads(t.data)

            instance.family = instance.family.strip()

            if instance.family in data:
                instance.order = data[instance.family]
                instance.save()

            if instance.family in data.values():
                instance.order = instance.family
                instance.save()

        except:
            pass

@receiver(pre_save, sender=Layer)
def update_colour(sender, instance, **kwargs):
    if instance.colour_munsell and not instance.colour:
        colour_link = instance.colour_munsell.colour_name.filter(is_default=True)
        if colour_link.exists():
            instance.colour = colour_link.first()
        else:
            instance.colour = instance.colour_munsell.colour_name.first()
    elif instance.colour and not instance.colour_munsell:
        munsell_link = instance.colour.munsell_value.filter(is_default=True)
        if munsell_link.exists():
            instance.colour_munsell = munsell_link.first()
        else:
            instance.colour_munsell = instance.colour.munsell_value.first()
    # unset the hex-colour
    if instance.colour_munsell == "" or not instance.colour_munsell:
        instance.colour_hex = None
    # set the hex-colour
    if instance.colour_munsell and instance.colour_munsell != "":
        try:
            colour_sRGB = colour.XYZ_to_RGB(colour.xyY_to_XYZ(colour.munsell_colour_to_xyY(instance.colour_munsell)), "sRGB")
            colour_RGB = [min(round(x), 255) for x in (colour.models.eotf_inverse_sRGB(colour_sRGB) * 255)] # linearise sRGB values and convert to integer RGB

            instance.colour_hex = "#%02x%02x%02x" % tuple(colour_RGB) # convert to hex and assign. we convert to hex, as it works better than RGB for html
        except: #except the case that the Munsell Color has a wrong specification..
            pass
