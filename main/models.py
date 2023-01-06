from django.db import models
from django.urls import reverse
from django.db.models import Q
import json

def get_classname(x):
    """
    For the templates, create classes from strings
    """
    import re
    return ''.join([y for y in x.lower() if bool(re.search('[a-z0-9]',y))])

class ContactPerson(models.Model):
    name = models.CharField('name', max_length=300)
    email = models.CharField('email',max_length=300)
    affiliation = models.CharField('affiliation', max_length=300, blank=True)
    tags = models.CharField('tag', max_length=300, blank=True, null=True)

    def __str__(self):
        return self.name

class Reference(models.Model):
    title = models.CharField('title', max_length=500)
    short = models.CharField('short', max_length=200, blank=True, null=True)
    tags = models.TextField('tags',blank=True)
    doi = models.CharField('doi', max_length=500)

    class Meta:
        ordering = ['short']

    def __str__(self):
        return self.short if self.short else self.title

    def get_absolute_url(self):
        return reverse('ref_add')

    @classmethod
    def filter(self, kw):
        return Reference.objects.filter(Q(short__contains=kw) | Q(title__contains=kw ) | Q(tags__contains=kw ))

    @property
    def link(self):
        if self.doi.startswith('http'):
            return self.doi
        else:
            return f'https://doi.org/{self.doi}'

    @property
    def scihub(self):
        if self.doi.startswith('http'):
            return self.doi
        else:
            return f'https://sci-hub.ee/{self.doi}'


class Synonym(models.Model):
    """For Layers that gets renamed - provide synonyms"""
    name = models.CharField('name', max_length=300)
    type = models.CharField('type', max_length=300, blank=True, null=True)

    def __str__(self):
        return self.name

class CheckpointLayerJunction(models.Model):
    layer = models.ForeignKey('Layer', verbose_name=u"layer", related_name='junction', null=True, blank=True, on_delete=models.CASCADE)
    checkpoint = models.ForeignKey('Checkpoint', verbose_name=u'checkpoint', related_name='junction',null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        if self.layer:
            return str(self.layer)
        return str(self.checkpoint)

    @property
    def model(self):
        if self.layer:
            return self.layer
        return self.checkpoint


class RelativeDate(models.Model):
    relation = models.ForeignKey(CheckpointLayerJunction, verbose_name=u'relation', on_delete=models.CASCADE)
    how = models.CharField('how', max_length=20, choices=[('same','Same Age'),('younger', 'Younger'),('older', 'Older')])
    offset = models.IntegerField('offset', default=0)
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)

    def __str__(self):
        return f"{self.how}:{self.relation}"

    #the upper and lower values are just set to 10k away from the reference point
    #this is just for display, so that they can fade out
    @property
    def upper(self):
        if self.how == 'same':
            return self.relation.model.mean_upper + self.offset
        elif self.how == 'older':
            return self.relation.model.mean_upper + 1000 + self.offset
        else:
            return self.relation.model.mean_lower - self.offset

    @property
    def lower(self):
        if self.how == 'same':
            return self.relation.model.mean_lower + self.offset
        elif self.how == 'older':
            return self.relation.model.mean_upper + self.offset
        else:
            return self.relation.model.mean_lower - 1000 - self.offset


class DatingMethod(models.Model):
    option = models.CharField('option', max_length=200)

    def __str__(self):
        return self.option

    class Meta:
        ordering = ['option']

class Date(models.Model):
    method = models.CharField('dating method', max_length=200)
    #this is uncalibrated if C14, otherwise just easy to enter
    estimate = models.IntegerField('estimate', blank=True, null=True)
    plusminus = models.IntegerField('plusminus', blank=True, null=True)
    oxa = models.CharField('oxa-code', max_length=300, blank=True, null=True)
    curve = models.CharField('calibration_curve', max_length=300, blank=True, null=True)
    #this is the 2 Sigma calibrated date if C14
    #should be the calender years in 1950BP
    upper = models.IntegerField('upper bound', blank=True, null=True)
    lower = models.IntegerField('lower bound', blank=True, null=True)
    #additional information
    description = models.TextField('description', blank=True, null=True)
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)

    @classmethod
    def table_columns(self):
        #human readable representation of the dates
        return  ['Layer','Method','Lab Code','Date','Error','Upper Bound','Lower Bound','Notes','Reference']


    def __str__(self):
        if self.method == '14C':
            if self.upper:
                return f"{self.upper:,} - {self.lower:,} BP"
            if self.estimate:
                return f"{self.estimate:,} ± {self.plusminus:,} uncal 14C"
        else:
            if not self.upper and not self.estimate and not self.lower:
                return 'Unset Date'
            if self.estimate and self.plusminus:
                return f"{self.estimate:,} ± {self.plusminus:,} ya"
            if self.estimate:
                return f"{self.estimate:,} ya"
            if self.upper and not self.lower:
                return f"< {self.upper:,} ya"
            if self.lower and not self.upper:
                return f"> {self.lower:,} ya"
            if self.upper != self.lower:
                return f"{self.upper:,} - {self.lower:,} ya"
            return f"{self.upper:,} ya"

class Location(models.Model):
    name = models.CharField('name', max_length=200)
    description = models.TextField('description', blank=True)
    geo = models.JSONField('geojson', blank=True, null=True)
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)

    def get_absolute_url(self):
        return reverse('location_update', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name


class Checkpoint(models.Model):
    name = models.CharField('name', max_length=200)
    description = models.TextField('description', blank=True)
    category = models.CharField('category', max_length=200,blank=True, null=True)
    type = models.CharField('type', max_length=200,blank=True, null=True)
    date = models.ManyToManyField(Date, verbose_name=u'date',blank=True)
    loc = models.ManyToManyField(Location, verbose_name=u"location", blank=True)
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)

    @classmethod
    def filter(self, kw):
        return Checkpoint.objects.filter(Q(name__contains=kw) | Q(type__contains=kw) | Q(description__contains=kw ))

    @property
    def mean_upper(self):
        return self.date.first().upper

    @property
    def mean_lower(self):
        return self.date.first().lower

    @property
    def age_summary(self):
        ## Todo: Make a real summary...
        if self.date.first():
            return self.date.first()
        return 'Date Unset'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('checkpoint_update', kwargs={'pk':self.id})

class Culture(models.Model):
    name = models.CharField('name', max_length=200)
    description = models.TextField('description', blank=True)
    hominin_group = models.CharField('hominin_group', max_length=500, blank=True)
    parent = models.ForeignKey('self', verbose_name=u'parent', related_name='child', blank=True, null=True, on_delete=models.SET_NULL)
    upper = models.IntegerField(blank=True, default=100000, null=True)
    lower = models.IntegerField(blank=True, default=0, null=True)
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)

    class Meta:
        ordering = ['-upper']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('culture_detail', kwargs={'pk':self.id})

    # Additional funcitons
    @classmethod
    def filter(self, kw):
        return Culture.objects.filter(Q(name__contains=kw) | Q(description__contains=kw ))

    @property
    def classname(self):
        return get_classname(self.name)

    @property
    def age_summary(self):
        return f"{self.upper:,} - {self.lower:,} ya"

    @property
    def children(self):
        return Culture.objects.filter(parent__id = self.id).all()

    def all_cultures(self, nochildren=False, noself=False):
        if not noself:
            cultures = list(Culture.objects.filter(pk=self.id).all())
        else:
            cultures = []
        children = list(Culture.objects.filter(parent__id = self.id).all())
        if len(children) == 0 or nochildren: #lowest branch
            return cultures
        # else: walk down the branches
        else:
            for cult in children:
                cultures.extend(cult.all_cultures())
        return cultures

    def all_sites(self, nochildren=False):
        sites = []
        for cult in self.all_cultures(nochildren=nochildren):
            sites.extend(
                [(cult, site) for site in Site.objects.filter(layer__culture__pk=cult.pk).all()]
            )
        return sites


class Epoch(models.Model):
    name = models.CharField('name', max_length=200)
    description = models.TextField('description', blank=True)
    date = models.ManyToManyField(Date, verbose_name =u"date")
    parent = models.ForeignKey('self', verbose_name=u'parent', related_name='child', null=True, blank=True, on_delete=models.SET_NULL)
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)

    class Meta:
        ordering = ['date__upper']

    @classmethod
    def filter(self, kw):
        return Epoch.objects.filter(Q(name__contains=kw) | Q(description__contains=kw ))

    @property
    def age_summary(self):
        ## Todo: Make a real summary...
        if self.date.first():
            return self.date.first()
        return 'Date Unset'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('epoch_list')


class Gallery(models.Model):
    title = models.CharField("title",max_length=200, blank=True, null=True)

def get_image_path(instance, filename):
    # instance = Image instance
    # filename = original filename
    return f'descr/{instance.gallery.model.model}/{instance.gallery.model.name.replace(" ","_")}/{filename.replace(" ","_")}'

class Image(models.Model):
    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE)
    image = models.ImageField('image', upload_to=get_image_path)
    title = models.CharField("title", max_length=200, blank=True)
    alt = models.TextField("alt", null=True, blank=True)

    def __str__(self):
        if self.title:
            return self.title
        return f"{self.gallery.title}.{self.image.name }"

class Site(models.Model):
    contact = models.ManyToManyField(ContactPerson, blank=True, verbose_name=u'contact', related_name='site')
    name = models.CharField('name', max_length=200)
    synonyms = models.ManyToManyField(Synonym, blank=True, verbose_name='synonym', related_name='site')
    country = models.CharField('country', max_length=200, blank=True)
    description = models.JSONField('description', blank=True, null=True)
    gallery = models.OneToOneField(Gallery, blank=True, null=True, verbose_name=u'gallery', related_name='model', on_delete=models.SET_NULL)
    type = models.CharField('type', max_length=200, blank=True)
    loc = models.ManyToManyField(Location, verbose_name=u"location")
    elevation = models.IntegerField('elevation', blank=True)
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def model(self):
        # this is for the description only, to send uploaded images to the correct model
        return 'site'

    @property
    def geometry(self):
        try:
            return json.loads(self.loc.first().geo)['features'][0]['geometry']
        except:
            return self.loc.first().geo['features'][0]['geometry']

    def lowest_date(self, cult=None, nochildren=False):
        try:
            if cult or nochildren:
                return max(x.lowest_date for x in Layer.objects.filter( Q(culture_id=cult) & Q(site_id = self.id) ).all())
            return max(x.lowest_date for x in self.layer.all())
        except:
            return -1

    def get_absolute_url(self):
        return reverse('site_detail', kwargs={'pk': self.pk})

    @property
    def checkpoints(self):
        return Checkpoint.objects.filter(layer__in=self.layer.all()).all()

    @property
    def cultures(self):
        return set([x.culture for x in self.layer.all()])

    @property
    def model(self):
        return 'site'

class Profile(models.Model):
    name = models.CharField('name', max_length=200)
    site = models.ForeignKey(Site, verbose_name=u'site', on_delete=models.PROTECT, related_name='profile')
    type = models.CharField('type', max_length=200, blank=True)

    def __str__(self):
        return f"{self.site.name}: {self.name}"

    @property
    def other_layers(self):
        return Layer.objects.filter(Q(site=self.site)).exclude(profile=self)

    @property
    def other_profiles(self):
        return Profile.objects.filter(site=self.site).exclude(id=self.pk)


class Layer(models.Model):
    name = models.CharField('name', max_length=200)
    synonyms = models.ManyToManyField(Synonym, blank=True, verbose_name='synonym', related_name='layer')
    parent = models.ForeignKey('self', verbose_name='parent layer', related_name='child', blank=True, null=True, on_delete=models.SET_NULL)
    unit = models.CharField('unit', max_length=300, blank=True, null=True)
    description = models.TextField('description', blank=True)
    site_use = models.TextField('site use', blank=True)
    characteristics = models.TextField('characteristics', blank=True)
    profile = models.ManyToManyField(Profile, verbose_name='profile', related_name='layer')
    site = models.ForeignKey(Site, verbose_name=u'site', related_name='layer', on_delete=models.CASCADE, blank=True, null=True)
    pos = models.IntegerField('position in profile')
    culture = models.ForeignKey(Culture, verbose_name=u"culture", related_name='layer', on_delete=models.PROTECT, blank=True, null=True)
    epoch = models.ForeignKey(Epoch, verbose_name=u"epoch", related_name='layer', on_delete=models.PROTECT, blank=True, null=True)
    checkpoint = models.ManyToManyField(Checkpoint, verbose_name=u'checkpoint', blank=True, related_name='layer')
    date = models.ManyToManyField(Date, verbose_name=u"date", blank=True, related_name='model')
    reldate = models.ManyToManyField(RelativeDate, verbose_name='relative date', blank=True)
    mean_upper = models.IntegerField(blank=True, default=1000000)
    mean_lower = models.IntegerField(blank=True, default=0)
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True, related_name='layer')

    class Meta:
        ordering = ['pos']

    def get_upper_sibling(self):
        return Layer.objects.filter(Q(pos__lt = self.pos) & Q(site=self.site) &
            (Q(date__isnull=False) | Q(checkpoint__isnull=False))  ).last()

    def get_lower_sibling(self):
        return Layer.objects.filter(Q(pos__gt = self.pos) & Q(site=self.site) &
            (Q(date__isnull=False) | Q(checkpoint__isnull=False)) ).first()

    @property
    def unit_class(self):
        return get_classname(self.unit)

    @property
    def lowest_date(self):
        """For sorting Layers by date, get all Dates and return the minimum"""
        if self.mean_upper:
            return self.mean_upper
        return -1

    @property
    def checkpoints(self):
        return [x for x in self.checkpoint.all()]

    @property
    def in_profile(self):
        return ",".join([x.name for x in self.profile.all()])

    def __str__(self):
        if self.site:
            return f"{self.site.name}:{self.name}"
        return f"Unset:{self.name}"

    @property
    def model(self):
        return 'layer'

    @property
    def age_summary(self):
        if dates := self.date.all():
            if len(dates)==1:
                return dates.first()
        return Date(upper=self.mean_upper, lower=self.mean_lower)

    def get_absolute_url(self):
        return f"{reverse('site_detail', kwargs={'pk':self.site.id})}#profile"

class Sample(models.Model):
    name = models.CharField('name', max_length=200)
    synonyms = models.ManyToManyField(Synonym, blank=True, verbose_name='synonym', related_name='sample')
    description = models.TextField('description', blank=True)
    layer = models.ForeignKey(Layer, verbose_name=u"layer", related_name='sample', on_delete=models.PROTECT)
    date = models.ManyToManyField(Date, verbose_name=u"date", blank=True)
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)

    @property
    def model(self):
        return 'sample'

class MammalianAssemblage(models.Model):
    layer = models.ForeignKey(Layer, verbose_name=u'layer', related_name='mammalian_assemblage', blank=True, on_delete=models.CASCADE)
    mammals = models.TextField('mammals', blank=True)
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)

models = {
    'site': Site,
    'culture':Culture,
    'layer': Layer,
    'date': Date,
    'synonym': Synonym,
    'profile':Profile,
    'epoch':Epoch,
    'checkpoint':Checkpoint,
    'reference':Reference
}