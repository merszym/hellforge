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
    title = models.CharField('title', max_length=200)
    short = models.CharField('short', max_length=200, blank=True, null=True)
    tags = models.TextField('tags',blank=True)
    doi = models.CharField('doi', max_length=200)

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

class Date(models.Model):
    upper = models.IntegerField('upper bound')
    lower = models.IntegerField('lower bound')
    method = models.CharField('dating method', max_length=200)
    description = models.TextField('description', blank=True)
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)

    def get_absolute_url(self):
        return reverse('date_update', kwargs={'pk': self.id})

    def __str__(self):
        return f"{self.upper:,} - {self.lower:,} ya"

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
    mean_upper = models.IntegerField(blank=True, default=100000)
    mean_lower = models.IntegerField(blank=True, default=0)
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
    date = models.ManyToManyField(Date, verbose_name =u"date")
    parent = models.ForeignKey('self', verbose_name=u'parent', related_name='child', blank=True, null=True, on_delete=models.SET_NULL)
    mean_upper = models.IntegerField(blank=True, default=100000)
    mean_lower = models.IntegerField(blank=True, default=0)
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)

    class Meta:
        ordering = ['mean_upper']

    @property
    def lowest_date(self):
        """For sorting cultures by date, get all layers assigned to that culture and return the minimum"""
        try:
            return max(x.lowest_date for x in self.layer.all())
        except:
            return -1


    @property
    def all_cultures(self):
        #TODO: recursively go through all children!
        return Culture.objects.filter(Q(pk=self.id) | Q(parent__id = self.id))

    @property
    def age_summary(self):
        ## Todo: Make a real summary...
        if self.date.first():
            return self.date.first()
        return 'Date Unset'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('culture_update', kwargs={'pk':self.id})

class Epoch(models.Model):
    name = models.CharField('name', max_length=200)
    description = models.TextField('description', blank=True)
    date = models.ManyToManyField(Date, verbose_name =u"date")
    parent = models.ForeignKey('self', verbose_name=u'parent', related_name='child', null=True, blank=True, on_delete=models.SET_NULL)
    mean_upper = models.IntegerField(blank=True, default=1000000)
    mean_lower = models.IntegerField(blank=True, default=0)
    loc = models.ManyToManyField(Location, verbose_name=u"location")
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)

    class Meta:
        ordering = ['mean_upper']

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

class Site(models.Model):
    contact = models.ManyToManyField(ContactPerson, blank=True, verbose_name=u'contact', related_name='site')
    name = models.CharField('name', max_length=200)
    country = models.CharField('country', max_length=200, blank=True)
    description = models.TextField('description', blank=True)
    type = models.CharField('type', max_length=200, blank=True)
    loc = models.ManyToManyField(Location, verbose_name=u"location")
    elevation = models.IntegerField('elevation', blank=True)
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def geometry(self):
        try:
            geo = json.loads(self.loc.first().geo)
        except:
            geo = self.loc.first().geo
        return geo['features'][0]['geometry']

    def lowest_date(self, cult=None):
        if cult:
            layers = Layer.objects.filter( Q(culture_id=cult) & Q(site_id = self.id) )
            if layers:
                return max(x.lowest_date for x in layers.all())
            return -1


    def get_absolute_url(self):
        return reverse('site_detail', kwargs={'pk': self.pk})

    @property
    def checkpoints(self):
        return Checkpoint.objects.filter(layer__in=self.layer.all()).all()

    @property
    def cultures(self):
        return set([x.culture for x in self.layers])

    @property
    def layers(self):
        layers = [x for x in self.layer.all()]
        return sorted(list(set(layers)), key=lambda x: x.pos)


class Profile(models.Model):
    name = models.CharField('name', max_length=200)
    site = models.ForeignKey(Site, verbose_name=u'site', on_delete=models.PROTECT, related_name='profile')
    type = models.CharField('type', max_length=200, blank=True)

    def __str__(self):
        return f"{self.site.name}: {self.name}"

    @property
    def other_layers(self):
        layers = []
        for layer in self.site.layer.all():
            if layer not in self.layer.all():
                layers.append(layer)
        return set(layers)

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
    date = models.ManyToManyField(Date, verbose_name=u"date", blank=True)
    mean_upper = models.IntegerField(blank=True, default=1000000)
    mean_lower = models.IntegerField(blank=True, default=0)
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)

    class Meta:
        ordering = ['pos']

    def get_upper_sibling(self):
        return self.site.layers.filter(pos > self.pos).first()

    def get_lower_sibling(self):
        return self.site.layers.filter(pos < self.pos).first()

    @property
    def lowest_date(self):
        """For sorting Layers by date, get all Dates and return the minimum"""
        # try direct dating:
        if self.date.first():
            return max(x.upper for x in self.date.all())
        if self.mean_upper:
            return self.mean_upper
        #TODO: test
        return 20000

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
        ## Todo: Make a real summary...
        if self.date.first():
            return self.date.first()
        if self.culture:
            return self.culture.date.first()
        if self.epoch:
            return self.epoch.date.first()
        return 'Unset'

    @property
    def age_depth(self):
        ## Todo: Make a real summary...
        if self.date.first():
            return 'direct dating'
        if self.culture:
            return 'culture'
        if self.epoch:
            return 'epoch'
        return 'Unset'

    def get_absolute_url(self):
        return reverse('site_detail', kwargs={'pk':self.site.id})

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