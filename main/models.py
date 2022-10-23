from django.db import models
from django.urls import reverse
from django.db.models import Q

class Reference(models.Model):
    title = models.CharField('title', max_length=200)
    short = models.CharField('short', max_length=200, blank=True, null=True)
    tags = models.TextField('tags',blank=True)
    doi = models.CharField('doi', max_length=200)
    pdf = models.FileField('pdf', upload_to='papers/', blank=True, null=True)

    def __str__(self):
        return self.short if self.short else self.title

    def get_absolute_url(self):
        return reverse('ref_add')

class Date(models.Model):
    upper = models.IntegerField('upper bound')
    lower = models.IntegerField('lower bound')
    method = models.CharField('dating method', max_length=200)
    description = models.TextField('description', blank=True)
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)

    def get_absolute_url(self):
        return reverse('date_update', kwargs={'pk': self.id})

    def __str__(self):
        return f"{self.upper:,} - {self.lower:,} kya"

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


class Culture(models.Model):
    name = models.CharField('name', max_length=200)
    description = models.TextField('description', blank=True)
    hominin_group = models.CharField('hominin_group', max_length=500, blank=True)
    date = models.ManyToManyField(Date, verbose_name =u"date")
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
        return reverse('culture_update', kwargs={'pk':self.id})

class Epoch(models.Model):
    name = models.CharField('name', max_length=200)
    description = models.TextField('description', blank=True)
    date = models.ManyToManyField(Date, verbose_name =u"date")
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
    name = models.CharField('name', max_length=200)
    description = models.TextField('description', blank=True)
    type = models.CharField('type', max_length=200, blank=True)
    loc = models.ManyToManyField(Location, verbose_name=u"location")
    elevation = models.IntegerField('elevation', blank=True)
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('site_detail', kwargs={'pk': self.pk})

    @property
    def layers(self):
        layers = []
        for profile in self.profile.all():
            for layer in profile.layer.all():
                layers.append(layer)
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
        for profile in self.site.profile.exclude(id=self.pk).all():
            for layer in profile.layer.all():
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
    pos = models.IntegerField('position in profile')
    culture = models.ForeignKey(Culture, verbose_name=u"culture", related_name='layer', on_delete=models.PROTECT, blank=True, null=True)
    epoch = models.ForeignKey(Epoch, verbose_name=u"epoch", related_name='layer', on_delete=models.PROTECT, blank=True, null=True)
    checkpoint = models.ManyToManyField(Checkpoint, verbose_name=u'checkpoint', blank=True)
    date = models.ManyToManyField(Date, verbose_name=u"date", blank=True)
    mean_upper = models.IntegerField(blank=True, default=1000000)
    mean_lower = models.IntegerField(blank=True, default=0)
    ref = models.ManyToManyField(Reference, verbose_name=u"reference", blank=True)

    class Meta:
        ordering = ['pos']

    @property
    def in_profile(self):
        return ",".join([x.name for x in self.profile.all()])

    @property
    def site(self):
        sites = [x.site for x in self.profile.all()]
        if len(sites)>0:
            return sites[0]
        else:
            return Site(name='unset')

    def __str__(self):
        return f"{self.site.name}:{self.name}"

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
        site = self.site
        print(site)
        return reverse('site_detail', kwargs={'pk':site.id})

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