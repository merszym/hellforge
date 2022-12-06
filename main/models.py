from django.db import models
from django.urls import reverse
from django.db.models import Q
import json


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

    def __str__(self):
        return self.short if self.short else self.title

    def get_absolute_url(self):
        return reverse('ref_add')

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


class DatingMethod(models.Model):
    option = models.CharField('option', max_length=200)

    def __str__(self):
        return self.option

class Date(models.Model):
    estimate = models.IntegerField('estimate', blank=True, null=True)
    plusminus = models.IntegerField('plusminus', blank=True, null=True)
    upper = models.IntegerField('upper bound', blank=True, null=True)
    lower = models.IntegerField('lower bound', blank=True, null=True)
    method = models.CharField('dating method', max_length=200)
    description = models.TextField('description', blank=True)
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)

    def get_absolute_url(self):
        return reverse('date_update', kwargs={'pk': self.id})

    def __str__(self):
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
    loc = models.ManyToManyField(Location, verbose_name=u"location")
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)

    class Meta:
        ordering = ['date__upper']

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
    country = models.CharField('country', max_length=200, blank=True)
    new_description = models.JSONField('new_description', blank=True, null=True)
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
    def has_related_site(self):
        for layer in self.layer.all():
            if len(layer.related.all()) > 0:
                return True
        return False


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
    description = models.TextField('description', blank=True)
    site_use = models.TextField('site use', blank=True)
    characteristics = models.TextField('characteristics', blank=True)
    profile = models.ManyToManyField(Profile, verbose_name='profile', related_name='layer')
    site = models.ForeignKey(Site, verbose_name=u'site', related_name='layer', on_delete=models.CASCADE, blank=True, null=True)
    pos = models.IntegerField('position in profile')
    culture = models.ForeignKey(Culture, verbose_name=u"culture", related_name='layer', on_delete=models.PROTECT, blank=True, null=True)
    epoch = models.ForeignKey(Epoch, verbose_name=u"epoch", related_name='layer', on_delete=models.PROTECT, blank=True, null=True)
    checkpoint = models.ManyToManyField(Checkpoint, verbose_name=u'checkpoint', blank=True, related_name='layer')
    related = models.ManyToManyField('self', verbose_name=u'related layers', blank=True)
    date = models.ManyToManyField(Date, verbose_name=u"date", blank=True, related_name='model')
    mean_upper = models.IntegerField(blank=True, default=1000000)
    mean_lower = models.IntegerField(blank=True, default=0)
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)

    class Meta:
        ordering = ['pos']

    def get_upper_sibling(self):
        return Layer.objects.filter(Q(pos__lt = self.pos) & Q(site=self.site) &
            (Q(date__isnull=False) | Q(checkpoint__isnull=False))  ).last()

    def get_lower_sibling(self):
        return Layer.objects.filter(Q(pos__gt = self.pos) & Q(site=self.site) &
            (Q(date__isnull=False) | Q(checkpoint__isnull=False)) ).first()

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
    def age_summary(self):
        if dates := self.date.all():
            if len(dates)==1:
                return dates.first()
        return Date(upper=self.mean_upper, lower=self.mean_lower)

    def get_absolute_url(self):
        return f"{reverse('site_detail', kwargs={'pk':self.site.id})}#profile"

class Sample(models.Model):
    name = models.CharField('name', max_length=200)
    description = models.TextField('description', blank=True)
    layer = models.ForeignKey(Layer, verbose_name=u"layer", related_name='sample', on_delete=models.PROTECT)
    date = models.ManyToManyField(Date, verbose_name=u"date", blank=True)
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)

class MammalianAssemblage(models.Model):
    layer = models.ForeignKey(Layer, verbose_name=u'layer', related_name='mammalian_assemblage', blank=True, on_delete=models.CASCADE)
    mammals = models.TextField('mammals', blank=True)
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)