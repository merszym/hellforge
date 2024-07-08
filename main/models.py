import json
from django.db import models
from django.urls import reverse
from django.db.models import Q
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
    password = models.TextField("password", blank=True, null=True)
    namespace = models.CharField(
        "slug", max_length=300, unique=True, blank=True, null=True
    )
    project_description = GenericRelation(
        "Description", related_query_name="project_project"
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("main_project_detail", kwargs={"namespace": self.namespace})

    @property
    def model(self):
        return "project"

    def get_data(self):
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

    @property
    def affiliations(self):
        affs = []
        for author in self.author.all():
            for affiliation in author.person.affiliation.all():
                if affiliation not in affs:
                    affs.append(affiliation)
        affs = [(x, n) for n, x in enumerate(affs, 1)]
        return affs

    @property
    def authors(self):
        authors = []
        affs = {x: n for (x, n) in self.affiliations}
        for author in self.author.all():
            aff_string = []
            for affiliation in author.person.affiliation.all():
                aff_string.append(str(affs[affiliation]))
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
        return f"{self.person.name}"


class Person(models.Model):
    name = models.CharField("name", max_length=300)
    email = models.CharField("email", max_length=300, default="placeholder@fill.me")
    affiliation = models.ManyToManyField(
        "Affiliation", blank=True, related_name="person", verbose_name="affiliation"
    )
    orcid = models.CharField("orcid_id", max_length=300, blank=True, null=True)
    tags = models.CharField("tags", max_length=300, blank=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("main_person_list")

    @classmethod
    def filter(self, kw):
        return Person.objects.filter(
            Q(name__contains=kw)
            | Q(email__contains=kw)
            | Q(tags__contains=kw)
            | Q(orcid__contains=kw)
            | Q(affiliation__name__contains=kw)
        )

    def get_data(self):
        # for an entry, return a dict {'col': data} that is used for the export of the data
        data = {
            "Contact Name": self.name,
            "Contact Email": self.email,
            "Contact Affiliations": ";".join([x.name for x in self.affiliation.all()]),
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

    class Meta:
        ordering = ["short"]

    def __str__(self):
        return self.short if self.short else self.title

    def get_absolute_url(self):
        return reverse("ref_add")

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
    def layer(self):
        if self.layer_model:
            return self.layer_model.first()
        # if sample not layer
        return self.sample_model.first().layer

    class Meta:
        default_manager_name = "visible_objects"
        ordering = ["upper"]

    @classmethod
    def table_columns(self):
        # human readable representation of the dates
        return [
            "Layer",
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

    def get_data(self):
        # for an entry, return a dict {'col': data} that is used for the export of the data
        data = {
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

            if self.estimate:
                # or uncalibrated
                return f"{self.estimate:,} ± {self.plusminus:,} BP"

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
        if self.model == "sample" and self.layer:
            return self.layer.age_summary()

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
    def layer_hierarchies(self):
        return sorted(
            list(set([x.hierarchie for x in self.layer.all() if x.hierarchie > 1]))
        )

    @property
    def cultures(self):
        return set([x.culture for x in self.layer.all()])

    @property
    def model(self):
        return "site"

    @classmethod
    def filter(self, kw):
        return Site.objects.filter(Q(name__contains=kw) | Q(country__contains=kw))

    def get_data(self):
        # for an entry, return a dict {'col': data} that is used for the export of the data
        # dont include sample or project - that is exported with the respective query
        data = {
            "Site Name": self.name,
            "Site Id": self.coredb_id,
            "Site Country": self.country,
            "Site Coordinates": f"{self.coordinates[0]},{self.coordinates[1]}",
        }
        return data

    @classmethod
    def table_columns(self):
        return ["Site Name", "Site Id", "Site Country", "Site Coordinates"]

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

    def get_dates(self):
        site_layers = self.layer.all()
        site_samples = Sample.objects.filter(layer__in=site_layers)
        return (
            Date.objects.filter(
                Q(hidden=False) & Q(layer_model__in=site_layers)
                | Q(sample_model__in=site_samples)
            )
            .order_by("layer_model")
            .distinct()
        )


class Profile(models.Model):
    name = models.CharField("name", max_length=200)
    site = models.ForeignKey(
        Site, verbose_name="site", on_delete=models.PROTECT, related_name="profile"
    )
    type = models.CharField("type", max_length=200, blank=True)

    def __str__(self):
        return f"{self.site.name}: {self.name}"

    @property
    def other_layers(self):
        return Layer.objects.filter(Q(site=self.site)).exclude(profile=self)

    @property
    def other_profiles(self):
        return Profile.objects.filter(site=self.site).exclude(id=self.pk)


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
    unit = models.CharField("unit", max_length=300, blank=True, null=True)
    description = models.TextField("description", blank=True)
    site_use = models.TextField("site use", blank=True)
    characteristics = models.TextField("characteristics", blank=True)
    profile = models.ManyToManyField(
        Profile, verbose_name="profile", related_name="layer"
    )
    site = models.ForeignKey(
        Site,
        verbose_name="site",
        related_name="layer",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    pos = models.IntegerField("position in profile")
    culture = models.ForeignKey(
        Culture,
        verbose_name="culture",
        related_name="layer",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    epoch = models.ForeignKey(
        Epoch,
        verbose_name="epoch",
        related_name="layer",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    #
    ## References
    #

    ref = models.ManyToManyField(
        Reference, verbose_name="reference", blank=True, related_name="layer"
    )

    class Meta:
        ordering = ["pos"]

    @property
    def parent(self):
        return self.layer

    @property
    def hierarchie(self):
        try:
            return 1 + max([y.hierarchie for y in self.child.all()])
        except ValueError:
            return 1

    @property
    def in_profile(self):
        return ",".join([x.name for x in self.profile.all()])

    def __str__(self):
        if self.site:
            return f"{self.site.name} ({self.name})"
        return f"{self.name}"

    @property
    def model(self):
        return "layer"

    def get_absolute_url(self):
        return f"{reverse('site_detail', kwargs={'pk':self.site.id})}#profile"

    def get_data(self):
        # for an entry, return a dict {'col': data} that is used for the export of the data
        # dont include site or project - that is exported with the respective query
        data = {
            "Layer Name": self.name,
            "Layer Age": self.age_summary(export=True),
            "Layer Culture": self.culture.name if self.culture else None,
            "Layer Umbrella Culture": (
                self.culture.get_highest().name if self.culture else None
            ),
            "Layer Epoch": self.epoch.name if self.epoch else None,
        }
        return data

    @classmethod
    def table_columns(self):
        # the table_columns for uploading and empty columns
        return [
            "Layer Name",
            "Layer Age",
            "Layer Culture",
            "Layer Umbrella Culture",
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

    def get_data(self):
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
    type = models.CharField("sample type", max_length=400, null=True, blank=True)
    name = models.CharField("name", max_length=200, null=True, blank=True)
    synonyms = models.ManyToManyField(
        Synonym, blank=True, verbose_name="synonym", related_name="sample"
    )
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
    # origin of samples
    # site for the cases, where the layer is yet unknown
    site = models.ForeignKey(
        Site,
        verbose_name="site",
        related_name="sample",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
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
        ordering = ["site", "batch", "layer__pos", "name"]

    def get_provenience(self):
        try:
            data = json.loads(self.provenience)
            return [(k, v) for k, v in data.items()]
        except:
            return []

    @property
    def model(self):
        return "sample"

    @property
    def samplebatch(self):
        return self.batch

    @classmethod
    def table_columns(self):
        return [
            "Sample Layer",
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

    def get_data(self):
        # for an entry, return a dict {'col': data} that is used for the export of the data
        # dont include layer or project - that is exported with the respective query
        infinite, upper, lower = self.get_upper_and_lower(calculate_mean=True)
        if upper == None and lower == None:
            infinite, upper, lower = self.layer.get_upper_and_lower(calculate_mean=True)
        if infinite:
            upper = None
        data = {
            "Sample Name": self.name,
            "Sample Synonyms": ";".join([str(x) for x in self.synonyms.all()]),
            "Sample Type": self.type,
            "Sample Year of Collection": self.year_of_collection,
            "Sample Provenience": ";".join(
                [f"{k}:{v}" for k, v in json.loads(self.provenience).items()]
            ),
            "Sample Age": self.age_summary(),
            "Sample Age Upper": upper,
            "Sample Age Lower": lower,
        }
        return data

    @property
    def project_namespaces(self):
        return [x.namespace for x in self.project.all()]


### The analyzed Sample section


class AnalyzedSample(models.Model):
    sample = models.ForeignKey(
        Sample, related_name="analyzed_sample", on_delete=models.PROTECT
    )
    library = models.CharField("library", max_length=200)
    probes = models.CharField("probes", max_length=200, blank=True, null=True)
    seqrun = models.CharField("sequencing run", max_length=400)
    project = models.ManyToManyField(
        Project, blank=True, verbose_name="project", related_name="analyzedsample"
    )
    metadata = models.JSONField("metadata", blank=True, null=True)
    tags = models.CharField("tags", blank=True, null=True, max_length=100)
    qc_pass = models.BooleanField("qc_pass", default=True)

    class Meta:
        unique_together = [["library", "seqrun"]]
        ordering = ["sample__site", "sample__layer", "sample", "seqrun", "probes"]

    def __str__(self):
        return f"{self.library}_{self.seqrun}"

    def get_data(self):
        # for an entry, return a dict {'col': data} that is used for the export of the data
        # dont include sample or project - that is exported with the respective query
        data = {
            "Library": self.library,
            "Capture Probe": self.probes,
            "Sequencing Run": self.seqrun,
            "Tag": self.tags,
            "QC": "Pass" if self.qc_pass else "Fail",
        }
        return data

    @property
    def site(self):
        return self.sample.site

    @property
    def layer(self):
        return self.sample.layer

    @property
    def samplebatch(self):
        return self.sample.batch

    @classmethod
    def table_columns(self):
        return [
            "Analyzed Sample",
            "Library",
            "Capture Probe",
            "Sequencing Run",
            "Tag",
            "QC",
        ]

    @property
    def project_namespaces(self):
        return [x.namespace for x in self.project.all()]

    @property
    def model(self):
        return "analyzedsample"


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
    def sample(self):
        return self.analyzedsample.sample

    @property
    def layer(self):
        return self.analyzedsample.sample.layer

    @property
    def site(self):
        return self.analyzedsample.sample.site

    def get_data(self):
        from main.tools.quicksand import get_data_for_export

        return get_data_for_export(self.data, self.version)


models = {
    "site": Site,
    "culture": Culture,
    "layer": Layer,
    "date": Date,
    "synonym": Synonym,
    "profile": Profile,
    "epoch": Epoch,
    "reference": Reference,
    "ref": Reference,
    "contact": Person,
    "person": Person,
    "affiliation": Affiliation,
    "description": Description,
    "author": Author,
    "project": Project,
    "sample": Sample,
    "samplebatch": SampleBatch,
    "analyzedsample": AnalyzedSample,
    "library": AnalyzedSample,
    "gallery": Gallery,
    "image": Image,
    "connection": Connection,
    "faunal_results": FaunalResults,
    "layeranalysis": LayerAnalysis,
    "quicksand_analysis": QuicksandAnalysis,
}
