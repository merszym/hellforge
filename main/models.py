import json
from django.db import models
from django.urls import reverse
from django.db.models import Q, CASCADE
from django.core.validators import RegexValidator
from django.contrib.contenttypes.fields import GenericForeignKey  # for the description
from django.contrib.contenttypes.models import ContentType  # for the description
from django.contrib.contenttypes.fields import GenericRelation
import re
import hashlib
import statistics



# In case models implement the 'hidden' attribute
class VisibleObjectManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(hidden=False)


def get_classname(x):
    """
    For the templates, create classes from strings
    """
    import re

    return "".join([y for y in x.lower() if bool(re.search("[a-z0-9]", y))])


#
# Project Model
#


class Project(models.Model):
    name = models.CharField("name", max_length=500, unique=True)
    published = models.BooleanField("published", default=False)
    year_of_publication = models.IntegerField('year_of_publication', blank=True, null=True)
    password = models.TextField("password", blank=True, null=True)
    namespace = models.CharField(
        "slug", max_length=300, unique=True, blank=True, null=True
    )
    project_description = GenericRelation(
        "Description", related_query_name="project_project"
    )
    ref = models.ManyToManyField(
        "Reference", verbose_name="reference", blank=True, related_name="project"
    )
    parameters = models.JSONField("parameters", blank=True, null=True)
    ena_accession = models.CharField("ENA Accession Id", max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("main_project_detail", kwargs={"namespace": self.namespace})

    @property
    def model(self):
        return "project"

    def get_data(self, **kwargs):
        # for an entry, return a dict {'col': data} that is used for the export of the data
        # dont include sample or project - that is exported with the respective query
        data = {
            "Project Name": self.name,
        }
        return data

    @property
    def public_password(self):
        if self.password:
            return hashlib.md5(self.password.encode()).hexdigest()
        return ""


#
# Description model
#


def get_image_path(instance, filename):
    # instance = the new Image instance
    # filename = the original filename
    if not instance.gallery.description:
        batch = instance.gallery.sample_batch
        site = batch.site
        # direct upload via gallery
        return f'batches/{site.name.replace(" ","_")}/{batch.classname}/{filename.replace(" ","_")}'
    description = instance.gallery.description
    object = description.content_object
    model = object.model
    if model == "project":
        name = object.namespace
    else:
        name = object.name
    try:
        project = description.project.first().namespace
        return f'descriptions/{model}/{name.replace(" ","_")}/{project}/{filename.replace(" ","_")}'
    except:
        return (
            f'descriptions/{model}/{name.replace(" ","_")}/{filename.replace(" ","_")}'
        )


class Image(models.Model):
    gallery = models.ForeignKey(
        "Gallery", on_delete=models.CASCADE, related_name="image"
    )
    image = models.ImageField("image", upload_to=get_image_path)
    title = models.CharField("title", max_length=200, blank=True)
    alt = models.TextField("alt", null=True, blank=True)

    @property
    def model(self):
        return "image"


class Gallery(models.Model):
    title = models.CharField("title", max_length=200, blank=True, null=True)
    description = models.OneToOneField(
        "Description",
        verbose_name="description",
        related_name="gallery",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    @property
    def model(self):
        return "gallery"


class Description(models.Model):
    content = models.JSONField("content", blank=True, null=True)
    ref = models.ManyToManyField(
        "Reference", verbose_name="reference", blank=True, related_name="description"
    )
    project = models.ManyToManyField(
        "Project", verbose_name="project", related_name="description"
    )

    # to link the description to other models
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, blank=True, null=True
    )
    object_id = models.PositiveIntegerField(
        null=True
    )  # null=True only for backwarts compability
    content_object = GenericForeignKey("content_type", "object_id")
    exclude_from_print = models.BooleanField("exclude_from_print", default=False)

    @property
    def affiliations(self):
        affs = []
        for author in self.author.all():
            for junction in author.person.affiliation.all():
                if junction.affiliation not in affs:
                    affs.append(junction.affiliation)
        affs = [(x, n) for n, x in enumerate(affs, 1)]
        return affs

    @property
    def authors(self):
        authors = []
        affs = {x: n for (x, n) in self.affiliations}
        for author in self.author.all():
            aff_string = []
            for junction in author.person.affiliation.all():
                aff_string.append(str(affs[junction.affiliation]))
            authors.append((author, ",".join(aff_string)))
        return authors

    @property
    def model(self):
        return "description"


class Connection(models.Model):
    link = models.CharField("link", max_length=300)
    name = models.CharField("name", max_length=500, null=True, blank=True)
    short_description = models.TextField("short_description", blank=True)


#
# / Description
#
class Affiliation(models.Model):
    name = models.CharField("name", max_length=1200)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

class AffiliationPersonJunction(models.Model):
    affiliation = models.ForeignKey("Affiliation", on_delete=models.CASCADE, related_name="person_junction")
    person = models.ForeignKey("Person", on_delete=models.CASCADE, related_name="affiliation_junction")
    position = models.IntegerField('Position')

    class Meta:
        ordering = ['position']


class Author(models.Model):
    person = models.ForeignKey(
        "Person",
        blank=True,
        null=True,
        verbose_name="person",
        related_name="author",
        on_delete=models.PROTECT,
    )
    position = models.IntegerField("position", default=1)
    description = models.ForeignKey(
        "Description",
        verbose_name="description",
        related_name="author",
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ["position"]

    def __str__(self):
        # return a meaningfull short name to project/Site
        description = self.description
        return_string = f"Authorship"
        
        # first, get the project can be not assigned a project if its a note or a culture
        n_projects = len(description.project.all())
        if n_projects == 0:
            # project-description?
            if project := description.project_project.first():
                return_string = f"{return_string} | {project.name} (Project Description)"
            # culture description?
            if culture := description.culture.first():
                return_string = f"{return_string} | {culture.name} (Culture Description)"
            # site notes
            if site := description.site.first():
                return_string = f"{return_string} | {site.name} (Site Notes)"

        elif n_projects == 1:
            project = description.project.first()
            # its the description of a site
            site = description.site.first()
            return_string = f"{return_string} | {project.name} | {site.name} (Site Description)"
        
        else:
            # we dont have this case yet, in theory a description could be linked to multiple projects, but actually I should remove that
            # feature and instead make that a foreign key field...
            for project in description.project.all():
                return_string = f"{return_string} | {project.name} (Multi-Use)"
        return return_string
    

class Person(models.Model):
    name = models.CharField("name", max_length=300)
    email = models.CharField("email", max_length=300, default="placeholder@fill.me")
    orcid = models.CharField("orcid_id", max_length=300, blank=True, null=True)
    tags = models.CharField("tags", max_length=300, blank=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("main_person_list")

    @property
    def affiliation(self):
        return self.affiliation_junction

    @classmethod
    def filter(self, kw):
        return Person.objects.filter(
            Q(name__contains=kw)
            | Q(email__contains=kw)
            | Q(tags__contains=kw)
            | Q(orcid__contains=kw)
            | Q(affiliation_junction__affiliation__name__contains=kw)
        )
    @classmethod
    def table_columns(self):
        return [
            "Contact Name",
            "Contact Email",
            "Contact Affiliations",
            "Contact ORCID",
        ]

    def get_data(self, **kwargs):
        # for an entry, return a dict {'col': data} that is used for the export of the data
        data = {
            "Contact Name": self.name,
            "Contact Email": self.email,
            "Contact Affiliations": ";".join([f"({x.position}) {x.affiliation.name}" for x in self.affiliation.all()]),
            "Contact ORCID": self.orcid,
        }
        return data

    class Meta:
        ordering = ["name"]


class Reference(models.Model):
    title = models.CharField("title", max_length=500)
    short = models.CharField("short", max_length=200, blank=True, null=True)
    tags = models.TextField("tags", blank=True)
    doi = models.CharField("doi", max_length=500)
    bibtex = models.TextField("bibtex", blank=True)
    parsedInline = models.CharField("parsedInline", max_length=500, blank=True, null=True)
    parsedHTML = models.TextField("parsedHTML", blank=True)

    class Meta:
        ordering = ["short"]

    def __str__(self):
        return self.short if self.short else self.title

    def get_absolute_url(self):
        return reverse("ref_update", kwargs={"pk": self.pk})

    @classmethod
    def filter(self, kw):
        return Reference.objects.filter(
            Q(short__contains=kw) | Q(title__contains=kw) | Q(tags__contains=kw)
        )

    @property
    def link(self):
        if self.doi.startswith("http"):
            return self.doi
        else:
            return f"https://doi.org/{self.doi}"

    @property
    def scihub(self):
        if self.doi.startswith("http"):
            return self.doi
        else:
            return f"https://sci-hub.ee/{self.doi}"


class Synonym(models.Model):
    """For Layers that gets renamed - provide synonyms"""

    name = models.CharField("name", max_length=300)
    type = models.CharField("type", max_length=300, blank=True, null=True)

    def __str__(self):
        return f"{self.type}:{self.name}"


class DatingMethod(models.Model):
    option = models.CharField("option", max_length=200)

    def __str__(self):
        return self.option

    class Meta:
        ordering = ["option"]


class Date(models.Model):
    method = models.CharField("dating method", max_length=200)
    # this is uncalibrated if C14, otherwise just easy to enter
    estimate = models.IntegerField("estimate", blank=True, null=True)
    plusminus = models.IntegerField("plusminus", blank=True, null=True)
    # sigma (luminescence) or CI (radiocarbon/bayesian)
    sigma = models.CharField("sigma/CI", blank=True, null=True, max_length=100)
    oxa = models.CharField("oxa-code", max_length=300, blank=True, null=True)
    curve = models.CharField("calibration_curve", max_length=300, blank=True, null=True)
    raw = models.JSONField("calibrationcurve_datapoints", null=True, blank=True)
    # the upper and lower bounds based on the point estimate + standard-deviations
    upper = models.IntegerField("upper bound", blank=True, null=True)
    lower = models.IntegerField("lower bound", blank=True, null=True)
    # additional information
    description = models.TextField("description", blank=True, null=True)
    ref = models.ManyToManyField(Reference, verbose_name="reference", blank=True)
    hidden = models.BooleanField("hidden", default=False)
    objects = models.Manager()
    visible_objects = VisibleObjectManager()

    @property
    def model(self):
        return "date"

    @property
    def test(self):
        return "date"

    @property
    def get_layer(self):
        if self.layer_model.first():
            return self.layer_model.first()
        # if sample not layer
        return self.sample_model.first().get_layer

    class Meta:
        default_manager_name = "visible_objects"
        ordering = ["upper"]

    @classmethod
    def table_columns(self):
        # human readable representation of the dates
        return [
            "Layer",
            "Fossil Remain",
            "Method",
            "Lab Code",
            "Date",
            "Error",
            "Sigma/CI",
            "Curve",
            "Upper Bound",
            "Lower Bound",
            "Notes",
            "Reference",
        ]

    def get_data(self, **kwargs):
        # for an entry, return a dict {'col': data} that is used for the export of the data
        data = {
            "Sample": self.sample_model.first().name if self.sample_model.first() else None,
            "Method": self.method,
            "Lab Code": self.oxa,
            "Date": self.estimate,
            "Error": self.plusminus,
            "Sigma/CI": self.sigma,
            "Curve": self.curve,
            "Upper Bound": self.upper,
            "Lower Bound": self.lower,
            "Notes": self.description,
            "Reference": self.ref.first(),
        }
        return data

    def get_upper(self):
        # is used to get the upper date or return the "infinite" if it doesnt exist
        return f"{self.upper:,}" if self.upper else f"> {self.lower:,}"

    def get_lower(self):
        # the lower should always exist
        return f"{self.lower:,}"

    def to_ms(self):
        if self.upper and self.lower:
            upper = self.upper * -31556952 - (1970 * 31556952000)
            lower = self.lower * -31556952 - (1970 * 31556952000)
            return upper, lower
        return False, False

    def get_polygon_css(self):
        # calculate the relative values for a css-polygon property
        # first Value is (0,100%) (100% bc. the points starts in the left upper corner), last one (100%, 100%)
        # The highest! value should thus have a y-property of 0%
        raw = json.loads(self.raw)
        # start with the x-values
        base = self.lower - self.upper  # the date range
        raw = [(x, y) for (x, y) in raw if (x < self.upper and x > self.lower)]
        raw = [(((x - self.upper) / base) * 100, y) for (x, y) in raw]
        # continue with the y values
        lower = min(list([y for (x, y) in raw]))
        upper = max(list([y for (x, y) in raw]))
        base = lower - upper
        if (
            base == 0
        ):  # same probabilities for all datapoints (near end of calibration curve)
            raw = [(x, 0) for (x, y) in raw]
        else:
            raw = [
                (x, round((y - lower) / base * 100, 3) + 100) for (x, y) in raw
            ]  # 0% is highest, 100% is lowest
        # append a 0 point at start and end to have an even bottomline
        raw.insert(0, (0, 100))
        raw.append((100, 100))
        polygon = " ".join([f"{x:.2f},{y:.2f}" for x, y in raw])
        return polygon  # f"clip-path: polygon({polygon})"

    def __str__(self):
        if self.method == "14C":
            if self.upper and self.lower:
                # this is calibrated
                return f"{self.upper:,} - {self.lower:,} calBP"

            if self.lower:
                # this is infinite age
                if self.curve:
                    # calibrated infinite
                    # currently not possible with iosacal
                    return f"> {self.lower:,} calBP"
                return f"> {self.lower:,} BP"

            if self.estimate and self.plusminus:
                # or uncalibrated
                return f"{self.estimate:,} ± {self.plusminus:,} BP"
            
            if self.estimate:
                # uploaded by accident without errors?
                return f"{self.estimate:,} ± N/A BP"

        elif self.method.strip() in [
            "OSL",
            "TL",
            "IRSL",
            "pIRIR225",
            "pIRIR",
            "TT-OSL",
            "ESR",
            "US-ESR",
        ]:
            # Luminescence dating
            # by convention reported in ka (from the time of measurement)
            if self.estimate and self.plusminus:
                return (
                    f"{round(self.estimate/1000,2)} ± {round(self.plusminus/1000,2)} ka"
                )
            if self.upper != self.lower:
                try:
                    return f"{round(self.upper/1000,2)} - {round(self.lower/1000,2)} ka"
                except TypeError:
                    return f"{self.upper} - {self.lower} years"  # this is for NoneType date, should not happen in normal cases
            return f"{self.upper} ka"

        else:
            if self.estimate and self.plusminus:
                return f"{self.estimate:,} ± {self.plusminus:,} years"
            if self.estimate:
                return f"{self.estimate:,} years"
            if self.upper and not self.lower:
                return f"< {self.upper:,} years"
            if self.lower and not self.upper:
                return f"> {self.lower:,} years"
            if self.upper != self.lower:
                return f"{self.upper:,} - {self.lower:,} years"
            return f"{self.upper:,} years"

    def is_used_as_limit(self):
        """prevent deletion/unlinking of a date, if it is set as a layer or sample boundary"""
        return any(
            [
                self.sample_upper_date.first(),
                self.sample_lower_date.first(),
                self.layer_upper_date.first(),
                self.layer_lower_date.first(),
            ]
        )


class Dateable(models.Model):

    #
    ## now this is the dating and age section for layers...
    #
    # hierarchy 1. Raw dates
    date = models.ManyToManyField(
        Date, verbose_name="date", blank=True, related_name="%(class)s_model"
    )
    # hierarchy 2. Define upper and lower Date objects
    date_upper = models.ForeignKey(
        Date,
        verbose_name="upper date",
        related_name="%(class)s_upper_date",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    date_lower = models.ForeignKey(
        Date,
        verbose_name="lower date",
        related_name="%(class)s_lower_date",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    # Intermediate hierarchy: calculated range from the dates in the layer OR from the upper and lower
    mean_upper = models.IntegerField(blank=True, null=True)
    mean_lower = models.IntegerField(blank=True, null=True)
    # Hierachy 3: Set the Age, overwrite everything else
    set_upper = models.IntegerField(blank=True, null=True)
    set_lower = models.IntegerField(blank=True, null=True)

    class Meta:
        abstract = True

    @property
    def undated(self):
        return not any(
            [
                self.set_upper,
                self.set_lower,
                self.date_upper,
                self.date_lower,
                self.date.first(),
            ]
        )

    def get_upper_and_lower(self, calculate_mean=False):
        """for a datable class, get the information about inifinite, upper and lower ends. Return computer readable tuple (infinite, upper, lower)"""
        infinite = False
        upper = None
        lower = None

        # start again with the first hierarchie
        if self.set_upper and self.set_lower:
            return infinite, self.set_upper, self.set_lower

        # 2. for the date_upper and date_lower values

        if self.date_upper and self.date_lower:
            lower = self.date_lower.lower
            infinite = self.date_upper.get_upper().startswith(">")

            # if upper is infinite, get the lower estimate of the inifininte
            upper = (
                self.date_upper.lower  # infinite dates dont have an upper value
                if infinite
                else self.date_upper.upper
            )
            return infinite, upper, lower

        # if only date_upper is set, it is not infinite
        if self.date_upper and not self.date_lower:
            lower = 1
            upper = self.date_upper.upper
            return infinite, upper, lower

        # if only date_lower is set, its beyond that date (inifinite)
        if self.date_lower and not self.date_upper:
            lower = self.date_lower.lower
            infinite = self.date_lower.get_upper().startswith(
                ">"
            )  # check if the DATE is infinite
            upper = self.date_lower.lower if infinite else self.date_lower.upper
            infinite = True  # set inifinite because its bigger than the lower date
            return infinite, upper, lower

        if self.model == 'sample' and self.sample:
            return self.sample.get_upper_and_lower(calculate_mean=calculate_mean)
        
        # 3. get the mean of the dates
        # this is most likely wrong...
        if calculate_mean:
            if self.date.first():
                all_upper = [x.upper for x in self.date.all() if x.upper]
                all_lower = [x.lower for x in self.date.all() if x.lower]

                # for dates that have only the lower value reported (>40000), add the date to the upper array as well
                all_upper.extend([x.lower for x in self.date.all() if x.upper == None])

                if len(all_upper) > 0:
                    upper = int(statistics.mean(all_upper))
                if len(all_lower) > 0:
                    lower = int(statistics.mean(all_lower))
                # make sure lower is older than upper
                # with dates beyond radiocarbon, this might happen (because only lower is reported)
                if lower > upper:
                    upper = lower
            return False, upper, lower

        return infinite, upper, lower

    def age_summary(self, export=False):      
        ## first, see if the bounds are set
        if self.set_upper and self.set_lower:
            return Date(upper=self.set_upper, lower=self.set_lower)
        ## then, check if there are dates
        # check if both are true
        if self.date_upper and self.date_lower:
            if self.date_upper == self.date_lower:
                return f"{self.date_upper}"
            # the upper could be infinite, but we dont care at this moment
            return (
                f"{self.date_upper.get_upper()} - {self.date_lower.get_lower()} years"
            )
        # check if ONE of the dates is set
        if self.date_upper:
            return f"< {self.date_upper}"

        if self.date_lower:
            if str(self.date_lower).startswith(">"):
                return f"{self.date_lower}"
            return f"> {self.date_lower}"

        ## else, get from dates
        if dates := self.date.all():
            if len(dates) == 1:
                if export:
                    return Date(upper=dates.first().upper, lower=dates.first().lower)
                return dates.first()
            else:
                return Date(upper=self.mean_upper, lower=self.mean_lower)

        ## if no dates, look if there is context
        if self.model == 'sample' and self.sample:
            return self.sample.age_summary(export=export)

        if self.model == "sample" and self.get_layer:
            return self.get_layer.age_summary()

        ## return "undated"
        else:
            if export:
                return None
            return "Undated"

    def update_boundaries(self):
        from main.tools import dating

        dating.recalculate_mean(self)

    @property
    def date_references(self):
        return Reference.objects.filter(date__in=self.date.all()).distinct()

    @property
    def hidden_dates(self):
        if self.model == "sample":
            return Date.objects.filter(Q(hidden=True) & Q(sample_model=self))
        return Date.objects.filter(Q(hidden=True) & Q(layer_model=self))


class Location(models.Model):
    name = models.CharField(
        "name", max_length=200, blank=True, null=True
    )  # gets assigned by the model using the loc
    description = models.TextField("description", blank=True)
    geo = models.JSONField("geojson", blank=True, null=True)
    ref = models.ManyToManyField(Reference, verbose_name="reference", blank=True)

    def get_coordinates(self):
        if self.geo:
            try:
                geo = json.loads(self.geo)
            except:
                geo = self.geo
            for feat in geo["features"]:
                if feat["geometry"]["type"] == "Point":
                    long, lat = feat["geometry"]["coordinates"]
                    return round(lat, 4), round(long, 4)
        return None, None

    def get_absolute_url(self):
        return reverse("location_update", kwargs={"pk": self.pk})

    def __str__(self):
        return self.name


class Culture(models.Model):
    name = models.CharField("name", max_length=200)
    description = GenericRelation(Description, related_query_name="culture")
    hominin_group = models.CharField("hominin_group", max_length=500, blank=True)
    culture = models.ForeignKey(
        "self",
        verbose_name="parent",
        related_name="child",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    upper = models.IntegerField(blank=True, default=100000, null=True)
    lower = models.IntegerField(blank=True, default=0, null=True)
    ref = models.ManyToManyField(
        Reference, verbose_name="reference", blank=True, related_name="culture"
    )

    class Meta:
        ordering = ["-upper"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("culture_detail", kwargs={"pk": self.id})

    # Additional funcitons
    @property
    def model(self):
        return "culture"

    @classmethod
    def filter(self, kw):
        return Culture.objects.filter(Q(name__contains=kw))

    @property
    def classname(self):
        return get_classname(self.name)

    @property
    def age_summary(self):
        if self.upper and self.lower:
            return f"{self.upper:,} - {self.lower:,} ya"
        return "-"

    @property
    def children(self):
        return Culture.objects.filter(culture__id=self.id).all()

    def all_cultures(self, nochildren=False, noself=False):
        if not noself:
            cultures = [self]
        else:
            cultures = []
        children = list(Culture.objects.filter(Q(culture=self)).all())
        if len(children) == 0 or nochildren:  # lowest branch
            return cultures
        # else: walk down the branches
        else:
            for cult in children:
                cultures.extend(cult.all_cultures())
        return cultures

    def get_highest(self):
        if not self.culture:
            return self
        return self.culture.get_highest()


class Epoch(models.Model):
    name = models.CharField("name", max_length=200)
    upper = models.IntegerField("upper", blank=True, null=True)
    lower = models.IntegerField("lower", blank=True, null=True)

    class Meta:
        ordering = ["upper"]

    @property
    def age_summary(self):
        if self.upper and self.lower:
            return f"{self.upper:,} - {self.lower:,}"
        return ""

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("landing")


class Site(models.Model):
    site = models.ForeignKey(
        "self",
        verbose_name="parent",
        related_name="child",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    visible = models.BooleanField(
        "visible", default=True
    )  # to edit the site without going live...
    coredb_id = models.CharField("coreDB Id", null=True, blank=True, max_length=4)
    contact = models.ManyToManyField(
        Person, blank=True, verbose_name="contact", related_name="site"
    )
    name = models.CharField("name", max_length=200)
    synonyms = models.ManyToManyField(
        Synonym, blank=True, verbose_name="synonym", related_name="site"
    )
    country = models.CharField("country", max_length=200, blank=True)
    type = models.CharField("type", max_length=200, blank=True)
    loc = models.ManyToManyField(Location, verbose_name="location")
    elevation = models.IntegerField("elevation", blank=True, null=True)
    annual_mean_temp = models.FloatField('annual_mean_temp', blank=True, null=True)
    annual_precipitation_sum = models.FloatField('annual_precipitation_sum', blank=True, null=True)
    climate_class = models.CharField("climate_class", max_length=200, blank=True)
    description = GenericRelation(Description, related_query_name="site")
    project = models.ManyToManyField("Project", related_name="site", blank=True)
    connections = models.ManyToManyField("Connection", related_name="site", blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def parent(self):
        return self.site

    @property
    def coordinates(self):
        return self.loc.first().get_coordinates()

    @property
    def geometry(self):
        if self.loc.first().geo:
            try:
                return json.loads(self.loc.first().geo)["features"][0]["geometry"]
            except:
                return self.loc.first().geo["features"][0]["geometry"]
        else:
            return None

    def lowest_date(self, cult=None, nochildren=False):
        try:
            if cult or nochildren:
                return max(
                    x.lowest_date
                    for x in Layer.objects.filter(
                        Q(culture_id=cult) & Q(site_id=self.id)
                    ).all()
                )
            return max(x.lowest_date for x in self.layer.all())
        except:
            return -1

    def get_absolute_url(self):
        return reverse("site_detail", kwargs={"pk": self.pk})

    @property
    def cultures(self):
        return set([x.culture for x in self.layer.all()])

    @property
    def model(self):
        return "site"

    @classmethod
    def filter(self, kw):
        return Site.objects.filter(Q(name__contains=kw) | Q(country__contains=kw))

    def get_data(self, **kwargs):
        # for an entry, return a dict {'col': data} that is used for the export of the data
        # dont include sample or project - that is exported with the respective query
        data = {
            "Site Name": self.name,
            "Site Id": self.coredb_id,
            "Site Country": self.country,
            "Site Coordinates": f"{self.coordinates[0]},{self.coordinates[1]}",
            "Site Type":self.type,
            "Site Elevation": self.elevation,
            "Site Annual Mean Temperature": self.annual_mean_temp,
            "Site Annual Precipitation Sum": self.annual_precipitation_sum,
            "Site Climate Class": self.climate_class
        }
        return data

    @classmethod
    def table_columns(self):
        return ["Site Name", "Site Id", "Site Country", "Site Coordinates","Site Type"]

    @classmethod
    def squash_data(self, queryset):
        data = {
            "Site Name": ";".join([x.name for x in queryset]),
            "Site Id": ";".join(
                [x.coredb_id if x.coredb_id else "N/A" for x in queryset]
            ),
            "Site Country": ";".join([x.country for x in queryset]),
            "Site Coordinates": ";".join(
                [f"{x.coordinates[0]},{x.coordinates[1]}" for x in queryset]
            ),
        }
        return data

    def get_location_features(self):
        try:
            sgeo = self.loc.first().geo
        except AttributeError:
            sgeo = None
        if type(sgeo) == str:
            sgeo = dict(json.loads(sgeo))
        if sgeo:
            site_view_url = reverse("site_detail", kwargs={"pk": self.pk})
            sgeo["features"][0]["properties"][
                "popupContent"
            ] = f"<strong>{self.name}</strong><br><a href={site_view_url} class=btn-link>Details</a>"
            sgeo["features"][0]["properties"]["id"] = f"{self.pk}"
            return sgeo
        else:
            return {}

    def get_dates(self, without_reference=False):
        site_layers = self.layer.all()
        site_samples = Sample.objects.filter(site=self)
        dates = Date.objects.all()
        if not without_reference:
            dates = dates.filter(ref__isnull=False)
        return (
            dates.filter(
                Q(hidden=False) & Q(layer_model__in=site_layers)
                | Q(sample_model__in=site_samples)
            )
            .order_by("layer_model")
            .distinct()
        )


class Profile(models.Model):
    name = models.CharField("name", max_length=200)
    site = models.ForeignKey(
        Site, verbose_name="site", on_delete=models.CASCADE, related_name="profile"
    )
    type = models.CharField("type", max_length=200, blank=True)
    visible = models.BooleanField(
        "visible", default=True
    )  # to edit the profile without going live... 

    def __str__(self):
        return f"{self.site.name}: {self.name}"

    @property
    def other_layers(self):
        return Layer.objects.filter(Q(site=self.site))

    @property
    def other_profiles(self):
        return Profile.objects.filter(site=self.site).exclude(id=self.pk)

    def get_data(self, **kwargs):
        # for an entry, return a dict {'col': data} that is used for the export of the data
        data = {
            "Profile Name": self.name,
        }
        return data
    
    @property
    def max_number_of_parents(self):
        """
        get the number of nested parents to reserve accordingly the number of columns in the profile-table
        """
        n = 1
        for junction in self.layer_junction.all():
            layer = junction.layer
            if layer.number_of_parents > n:
                n = layer.number_of_parents
        return n+1


    @classmethod
    def table_columns(self):
        return ["Profile Name"]

class ProfileLayerJunction(models.Model):
    profile = models.ForeignKey('Profile',
        verbose_name="profile",
        related_name="layer_junction",
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    layer = models.ForeignKey('Layer',
        verbose_name="layer",
        related_name="profile_junction",
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    position = models.IntegerField('Position', default=1)
    visible = models.BooleanField(
        "visible", default=True
    )  # to edit the junction without going live...

    class Meta:
        ordering = ["profile","position"]

    @classmethod
    def table_columns(self):
        # human readable representation of the dates
        return [
            "Profile",
            "Layer Parent",
            "Layer"
        ]

    def get_data(self, **kwargs):
        # for an entry, return a dict {'col': data} that is used for the export of the data
        data = {
            "Profile": self.profile.name,
            "Layer Parent": self.layer.get_highest().name,
            "Layer":self.layer.name,
        }
        return data

texture_choices = {x:x for x in [
    '',
    'Clay',
    'Clay Loam',
    'Sandy Clay',
    'Sandy Clay Loam',
    'Sandy Loam',
    'Sand/Silt',
    'Loam',
    'Loamy Sand',
    'Sand',
    'Silty Clay',
    'Silty Clay Loam',
    'Silt Loam',
    'Silt'
]}

class ColourName(models.Model):
    name = models.CharField(max_length=64)
    is_default = models.BooleanField(default=False)

class ColourMunsell(models.Model):
    colour_munsell = models.CharField(max_length=32)
    colour_name = models.ManyToManyField(ColourName, related_name="munsell_value")
    is_default = models.BooleanField(default=False)

class TextureCategory(models.Model):
    category = models.CharField(max_length=32)

class TextureKeyword(models.Model):
    texture = models.CharField(max_length=64)
    texture_category = models.ForeignKey(TextureCategory, on_delete=models.CASCADE, related_name="texture_category")

class Layer(Dateable):
    name = models.CharField("name", max_length=200)
    synonyms = models.ManyToManyField(
        Synonym, blank=True, verbose_name="synonym", related_name="layer"
    )
    layer = models.ForeignKey(
        "self",
        verbose_name="parent layer",
        related_name="child",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    description = models.TextField("description", blank=True)
    site_use = models.TextField("site use", blank=True)
    site = models.ForeignKey(
        Site,
        verbose_name="site",
        related_name="layer",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    culture = models.ForeignKey(
        Culture,
        verbose_name="culture",
        related_name="layer",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    additional_cultures = models.ManyToManyField(
        Culture,
        verbose_name="additional_cultures",
        related_name="layers",
        blank=True,
    )
    epoch = models.ForeignKey(
        Epoch,
        verbose_name="epoch",
        related_name="layer",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    # fields related to geological sediment properties
    #colour = models.CharField("colour",max_length=200, blank=True, null=True) # this is the "informal" name
    #colour_munsell = models.CharField(
    #    "colour_munsell",
    #    max_length=200,
    #    validators=[
    #        RegexValidator(
    #            regex=r'^[0-9]+(\.[0-9]+)?[A-Z]+\s+[1-9](\.[0-9]+)?/[0-9]+(\.[0-9]+)?$',
    #            message="Enter a valid Munsell Number in the format 8.75YR 4.5/3",
    #            code="invalid_registration",
    #        ),
    #    ],
    #    blank=True,
    #    null=True) # The Munsell Color Code
    colour = models.ForeignKey(ColourName, blank=True, null=True, on_delete=models.SET_NULL, related_name="colour")
    colour_munsell = models.ForeignKey(ColourMunsell, blank=True, null=True, on_delete=models.SET_NULL, related_name="munsell")
    #colour_hex = models.CharField("colour_rgb", max_length=200, blank=True, null=True) # The hex value calculated from Munsell
    texture = models.CharField("texture", max_length=200, blank=True, null=True, choices=texture_choices)
    texture_keyword = models.ForeignKey(TextureKeyword, blank=True, null=True, on_delete=models.SET_NULL, related_name="texture")

    #
    ## References
    #

    ref = models.ManyToManyField(
        Reference, verbose_name="reference", blank=True, related_name="layer"
    )

    class Meta:
        ordering = ['name']

    @property
    def parent(self):
        return self.layer

    def get_highest(self):
        if self.parent:
            return self.parent.get_highest()
        return self
    
    @property
    def number_of_parents(self):
        if not self.parent:
            return 0
        return 1 + self.parent.number_of_parents

    @property
    def in_profile(self):
        return ",".join(set([x.profile.name for x in self.profile_junction.all()]))

    def __str__(self):
        if self.site:
            return f"{self.site.name} ({self.name})"
        return f"{self.name}"

    @property
    def model(self):
        return "layer"

    def get_absolute_url(self):
        return f"{reverse('site_detail', kwargs={'pk':self.site.id})}#profile"

    def get_data(self, **kwargs):
        # for an entry, return a dict {'col': data} that is used for the export of the data
        # get the age of the layer
        infinite, upper, lower = self.get_upper_and_lower(calculate_mean=True)
        if infinite:
            upper = None

        data = self.site.get_data()
        data.update({
            "Layer Name": self.name,
            "Layer Parent": self.get_highest().name,
            "Layer Profile": self.in_profile,
            "Layer Colour": self.colour_munsell,
            "Layer Texture": self.texture,
            "Layer Age": self.age_summary(export=True),
            'Layer Upper':upper,
            'Layer Lower':lower,
            "Layer Umbrella Culture": (
                self.culture.get_highest().name if self.culture else None
            ),
            "Layer Culture": self.culture.name if self.culture else None,
            "Layer Culture (Mixed)": ",".join([x.name for x in self.additional_cultures.all()]),
            "Layer Epoch": self.epoch.name if self.epoch else None,
        })
        
        return data

    @classmethod
    def table_columns(self):
        # the table_columns for uploading and empty columns
        return [
            "Layer Name",
            "Layer Parent",
            "Layer Profile",
            "Layer Colour",
            "Layer Texture",
            "Layer Age",
            "Layer Umbrella Culture",
            "Layer Culture",
            "Layer Culture (Mixed)",
            "Layer Epoch",
        ]


class SampleBatch(models.Model):
    name = models.CharField("name", max_length=400, null=True, blank=True)
    site = models.ForeignKey(
        Site, verbose_name="site", on_delete=models.PROTECT, related_name="sample_batch"
    )
    sampled_by = models.CharField("sampled_by", max_length=400, null=True, blank=True)
    year_of_arrival = models.IntegerField("year_of_arrival", null=True, blank=True)
    gallery = models.OneToOneField(
        Gallery,
        related_name="sample_batch",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def classname(self):
        return get_classname(self.name)

    @property
    def model(self):
        return "samplebatch"

    def get_data(self, **kwargs):
        # for an entry, return a dict {'col': data} that is used for the export of the data
        # dont include sample or project - that is exported with the respective query
        data = {
            "Sample Batch Name": self.name,
            "Sample Batch Arrival": self.year_of_arrival,
        }
        return data

    @classmethod
    def table_columns(self):
        return ["Sample Batch Name", "Sample Batch Arrival"]


class Sample(Dateable):
    # here we combine two separate concepts
    # 1. A sample in the DNA-sense with an MPI EVA ID (or maybe from other publications?)
    # 2. A "sample" or "fossil" in the archaeological sense (e.g. Denisova 15)
    # so we need to also account for some special cases in either of the cases
    # I _know_ I should make abstract classes, but thats a bit too late now...
    
    #this is to differentiate these cases in the front-end
    # use domain="archaeology" for fossil remains
    domain = models.CharField('domain', default="mpi_eva", max_length=100)

    #required fields for the Fossil Remains tab
    hominin_group = models.CharField('hominin_group', null=True, blank=True, max_length=100)

    #this is now for all the samples
    type = models.CharField("sample type", max_length=400, null=True, blank=True)
    name = models.CharField("name", max_length=200, null=True, blank=True)
    synonyms = models.ManyToManyField(
        Synonym, blank=True, verbose_name="synonym", related_name="sample"
    )
    ## only for DNA samples
    project = models.ManyToManyField(
        Project, blank=True, verbose_name="project", related_name="sample"
    )
    batch = models.ForeignKey(
        SampleBatch,
        blank=True,
        null=True,
        verbose_name="sample_batch",
        related_name="sample",
        on_delete=models.PROTECT,
    )
    year_of_collection = models.IntegerField(
        "year of collection", blank=True, null=True
    )
    # description
    description = GenericRelation(Description, related_query_name="sample")
    note = models.TextField("note", blank=True, null=True)
    # origin of samples
    # case: DNA sample has bone (e.g. Denisova3) as the origin 
    sample = models.ForeignKey(
        'self', 
        related_name='child', 
        verbose_name='parent', 
        null=True, 
        blank=True, 
        on_delete=models.PROTECT
    )
    # site for the cases, where the layer is yet unknown
    site = models.ForeignKey(
        Site,
        verbose_name="site",
        related_name="sample",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    # main case for sediments - origin is a layer
    layer = models.ForeignKey(
        Layer,
        verbose_name="layer",
        related_name="sample",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    provenience = models.JSONField("provenience", blank=True, null=True)
    ref = models.ManyToManyField(
        Reference, verbose_name="reference", blank=True, related_name="sample"
    )

    class Meta:
        ordering = ["site", "batch", "layer", "sample__layer", "name"]

    def get_provenience(self):
        try:
            data = json.loads(self.provenience)
            return [(k, v) for k, v in data.items()]
        except:
            return []

    @property
    def get_layer(self):
        if self.sample:
            return self.sample.layer
        return self.layer

    @property
    def model(self):
        return "sample"

    @classmethod
    def table_columns(self):
        return [
            "Layer Name",
            "Fossil Remain",
            "Sample Name",
            "Sample Synonyms",
            "Sample Type",
            "Sample Year of Collection",
            "Sample Provenience",
            "Sample Age",
            "Sample Age Upper",
            "Sample Age Lower",
        ]

    def __str__(self):
        return self.name if self.name != None else self

    def get_data(self, project=None, **kwargs):
        # for an entry, return a dict {'col': data} that is used for the export of the data
        # get the age of the layer
        infinite, upper, lower = self.get_upper_and_lower(calculate_mean=True)
        if upper == None and lower == None:
            if self.get_layer:
                infinite, upper, lower = self.get_layer.get_upper_and_lower(
                    calculate_mean=True
                )
        if infinite:
            upper = None
        ## Inherit from sample parent
        if layer:= self.get_layer:
            data = layer.get_data()
        else:
            data = self.site.get_data()
            data.update({
                x:"" for x in Layer.table_columns()
            })
        data.update(self.batch.get_data())
        data.update({
            "Fossil Remain": self.sample.name if self.sample else None,
            "Sample Name": self.name,
            "Sample Synonyms": ";".join([str(x) for x in self.synonyms.all()]),
            "Sample Type": self.type,
            "Sample Year of Collection": self.year_of_collection if self.year_of_collection else self.sample.year_of_collection if self.sample else None,
            "Sample Provenience": ";".join(
                [f"{k}:{v}" for k, v in json.loads(self.provenience).items()]
            ) if self.provenience else None,
            "Sample Dating": 'Direct' if self.date.first() else 'Context',
            "Sample Dates": ",".join([x.oxa or str(x) for x in self.date.all()]) if self.date.first() else "",
            "Sample Age": self.age_summary(),
            "Sample Age Upper": upper,
            "Sample Age Lower": lower,
        })
        return data

    @property
    def project_namespaces(self):
        return [x.namespace for x in self.project.all()]


### The analyzed Sample section

class ProbeTranslationTable(models.Model):
    probes = models.CharField("probes", max_length=200, blank=True, null=True)
    content = models.CharField("content", max_length=500, blank=True, null=True)

    def __str__(self):
        return f"{self.probes} ({self.content})"


class AnalyzedSample(models.Model):
    sample = models.ForeignKey(
        Sample,
        related_name="analyzed_sample",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    lysate = models.CharField("Lysate Id", max_length=200, blank=True, null=True)
    enc_batch = models.CharField("ENC Batch", max_length=200, blank=True, null=True)
    library = models.CharField("library", max_length=200, blank=True, null=True)
    reamp_library = models.CharField("library", max_length=200, blank=True, null=True)
    molecules_qpcr = models.IntegerField("qPCR molecules", blank=True, null=True)
    efficiency = models.FloatField("Library Prep Efficiency", blank=True, null=True)
    lnc_batch = models.CharField("LNC Batch", max_length=200, blank=True, null=True)
    capture = models.CharField("capture", max_length=200, blank=True, null=True)
    probes = models.CharField("probes", max_length=200, blank=True, null=True)
    seqrun = models.CharField("sequencing run", max_length=400)
    lane = models.CharField("lane", max_length=50, default="lane1")
    seqpool = models.CharField("seqpool", max_length=50, blank=True, null=True)
    project = models.ManyToManyField(
        Project, blank=True, verbose_name="project", related_name="analyzedsample"
    )
    metadata = models.JSONField(
        "metadata", blank=True, null=True
    )  # this is the pool-report
    tags = models.CharField("tags", blank=True, null=True, max_length=100)
    qc_pass = models.BooleanField("qc_pass", default=True)
    ena_accession = models.CharField("ENA Accession Id", max_length=200, blank=True, null=True)

    class Meta:
        unique_together = [["library", "seqrun", "lane"]]
        ordering = ["seqrun", "library"]

    def __str__(self):
        return f"{self.library}_{self.seqrun}"

    def get_data(self, for_upload=False, **kwargs):
        # for an entry, return a dict {'col': data} that is used for the export of the data
        # if only for re-upload, include less information and the 'object' column
        if for_upload: # include object and pk and ommit additional fields
            try:
                data = {
                    'object':f"analyzedsample_{self.pk}",
                    'Sample Name':self.sample.name
                }
            except: #negative control
                data = {
                    'object':f"analyzedsample_{self.pk}",
                    'Sample Name':""
                }
        else: #include the full record
            try:
                data = self.sample.get_data()
            except: 
                #negative controls -> add the headers for the previous hierarchies
                data={x:'' for x in Sample.objects.first().get_data().keys()}
        # in each case, add object-level information
        data.update({
            "Lysate": self.lysate,
            "ENC Batch": self.enc_batch,
            "Library": self.library,
            "Reamp Library": self.reamp_library,
            "Molecules (qPCR)": self.molecules_qpcr,
            "Efficiency": self.efficiency,
            "LNC Batch": self.lnc_batch,
            "Capture": self.capture,
            "Capture Probe": self.probes,
            "Sequencing Run": self.seqrun,
            "Sequencing Lane": self.lane,
            "Sequencing Pool": self.seqpool,
            "Tag": self.tags,
            "QC": "Pass" if self.qc_pass else "Fail",
            "ENA Accession Id": self.ena_accession
        })
        if not for_upload:
            if self.quicksand_analysis.last():
                data.update(
                    self.quicksand_analysis.last().get_data(**kwargs, grouped=True)
                )
            else:
                data.update(
                    {x:"" for x in QuicksandAnalysis.table_columns()}
                )
            if self.matthias_analysis.last():
                data.update(
                    self.matthias_analysis.last().get_data()
                )
            else:
                data.update(
                    {x:"" for x in HumanDiagnosticPositions.table_columns()}
                )
        return data

    @classmethod
    def table_columns(self):
        return [
            "Sample Name",
            "Lysate",
            "ENC Batch",
            "Library",
            "Reamp Library",
            "LNC Batch",
            "Molecules (qPCR)",
            "Efficiency",
            "Capture",
            "Capture Probe",
            "Sequencing Run",
            "Sequencing Lane",
            "Sequencing Pool",
            "Tag",
            "QC",
            "ENA Accession Id"
        ]

    @property
    def project_namespaces(self):
        return [x.namespace for x in self.project.all()]

    @property
    def model(self):
        return "analyzedsample"
    
    @property
    def probes_str(self):
        try:
            return ProbeTranslationTable.objects.get(probes=self.probes)
        except:
            return self.probes

#
#
### The expected Taxa section
#
#
#


class Taxonomy(models.Model):
    # this class stores a taxonomy-file to fill faunal data
    # I use a super simple { 'Family':'Order } dict to fill the
    # Order based on the family-field in the FaunalResults Entries
    #
    type = models.CharField("Type", max_length=50, blank=True, null=True)
    data = models.JSONField("Taxonomy Data", blank=True, null=True)


class LayerAnalysis(models.Model):
    type = models.CharField("Type", max_length=50, blank=True, null=True)
    method = models.CharField("Method", max_length=100, blank=True, null=True)
    layer = models.ForeignKey(
        Layer,
        verbose_name="layer",
        related_name="layer_analysis",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    site = models.ForeignKey(
        Site,
        related_name="layer_analysis",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )  # this is for the cases where fauna is connected to a site only...
    culture = models.ForeignKey(
        Culture,
        related_name="layer_analysis",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    ref = models.ForeignKey(
        Reference,
        verbose_name="reference",
        related_name="layer_analysis",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )

    class Meta:
        unique_together = [["layer", "ref", "type"]]

    def __str__(self):
        return f"{self.layer if self.layer else self.site} / {self.ref}"
    

class FaunalResults(models.Model):
    order = models.CharField("order", max_length=400, blank=True, null=True)
    family = models.CharField("family", max_length=400, blank=True, null=True)
    scientific_name = models.CharField(
        "scientific name", max_length=400, blank=True, null=True
    )
    taxid = models.CharField("TaxID", max_length=100, blank=True, null=True)
    results = models.JSONField("Faunal Results", blank=True, null=True)
    analysis = models.ForeignKey(
        "LayerAnalysis",
        blank=True,
        null=True,
        related_name="faunal_results",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"{self.analysis}: ({self.family} / {self.scientific_name})"

    @classmethod
    def table_columns(self):
        return [
            "Site Name",
            "Layer Name",
            "Culture Name",
            "Reference",
            "Method",
            "Order",
            "Family",
            "Scientific Name",
            "TaxID",
        ]

    @property
    def data(self):
        return [
            (
                self.analysis.layer.site.name
                if self.analysis.layer
                else self.analysis.site.name
            ),
            self.analysis.layer.name if self.analysis.layer else None,
            self.analysis.culture.name if self.analysis.culture else None,
            self.analysis.ref.short if self.analysis.ref else None,
            self.analysis.method,
            self.order,
            self.family,
            self.scientific_name,
            self.taxid,
        ]


#
#
# quicksand results
#
#


class QuicksandAnalysis(models.Model):
    version = models.CharField("Version", max_length=100, blank=True, null=True)
    analyzedsample = models.ForeignKey(  # [[library, sequencing-run combination]]
        AnalyzedSample,
        verbose_name="analyzedsample",
        related_name="quicksand_analysis",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    data = models.JSONField("data", blank=True, null=True)

    @property
    def model(self):
        return 'quicksand'
    
    @classmethod
    def table_columns(self):
        return [
                "quicksand version",
                "ReadsRaw",
                "ReadsLengthfiltered",
                "ReadsIdentified",
                "ReadsMapped",
                "ReadsDeduped",
                "DuplicationRate",
                "ReadsBedfiltered",
                "SeqsInAncientTaxa",
                "Ancient",
                "AncientTaxa",
                "OtherTaxa",
                "Subsitutions"
            ]

    def get_data(self, grouped=False, **kwargs):
        if grouped: # this is appended to the analyzedsample and grouped by library
            from main.tools.quicksand import get_data_for_export

            return get_data_for_export(self.data, self.version, **kwargs)
        
        else:
            # To get the full unfiltered and ungrouped quicksand-reports
            # get the data from the analyzed sample (including the grouped quicksand data -.-)
            # and remove the diagnostic positions and the quicksand-summary columns from the dict
            cols_qs = QuicksandAnalysis.table_columns()
            cols_mm = HumanDiagnosticPositions.table_columns()
            remove = set(cols_qs) | set(cols_mm)

            project_data = {k: v for k, v in self.analyzedsample.get_data().items() if k not in remove}

            #get a list of dicts (one for each line in the report)
            self_data = [x[0] for x in json.loads(self.data).values()]
            full_record = []

            for entry in self_data:
                tmp = project_data.copy()
                tmp.update(entry)
                full_record.append(tmp)

            return full_record         

    class Meta:
        ordering = [
            "analyzedsample__sample__site",
            "analyzedsample__sample__layer",
            "analyzedsample__sample",
            "analyzedsample__seqrun",
            "analyzedsample__probes",
        ]

#
#
# Matthias summary script results
#
#

class HumanDiagnosticPositions(models.Model):
    version = models.CharField("Version", max_length=100, blank=True, null=True)
    analyzedsample = models.ForeignKey(  # [[library, sequencing-run combination]]
        AnalyzedSample,
        verbose_name="analyzedsample",
        related_name="matthias_analysis",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    data = models.JSONField("data", blank=True, null=True)
    
    class Meta:
        ordering = [
            "analyzedsample__sample__site",
            "analyzedsample__sample__layer",
            "analyzedsample__sample",
            "analyzedsample__seqrun",
            "analyzedsample__probes",
        ]

    @classmethod
    def table_columns(self):
        obj = HumanDiagnosticPositions.objects.first()
        return obj.get_data().keys()
    
    def get_data(self, **kwargs):
        exclude = [
            "DB_entry","QC","QC_comment","Comments","Project_used","RunID","IndexLibID","CapLibID","IndexLibIDCoreDB","CapLibIDCoreDB",
            "p7","p5","SampleID","ExtractID","SampleType","ExperimentType","Site","ProbeSet","Description"
        ]
        duplicates = ["Ancient"]
        data = json.loads(self.data)
        for k in exclude:
            data.pop(k, None)
        new_data = {(f"MM_{k}" if k in duplicates else k):v for k,v in data.items() } # preserve column names in data
        return new_data

#
#
# Classes for Colour and Texture Databases
#
#



models = {
    "site": Site,
    "culture": Culture,
    "layer": Layer,
    "date": Date,
    "synonym": Synonym,
    "profile": Profile,
    "profilelayerjunction":ProfileLayerJunction,
    "epoch": Epoch,
    "reference": Reference,
    "ref": Reference,
    "contact": Person,
    "person": Person,
    "affiliation": Affiliation,
    "description": Description,
    "author": Author,
    "affiliationjunction": AffiliationPersonJunction,
    "project": Project,
    "sample": Sample,
    "samplebatch": SampleBatch,
    "analyzedsample": AnalyzedSample,
    "gallery": Gallery,
    "image": Image,
    "connection": Connection,
    "faunal_results": FaunalResults,
    "layeranalysis": LayerAnalysis,
    "quicksand_analysis": QuicksandAnalysis,
    "quicksand": QuicksandAnalysis,
}
