from django import forms
from .models import Location, Reference, Site, Profile, Layer, Culture, Date, Epoch, Checkpoint, ContactPerson, Image, RelativeDate

class ProfileForm(forms.ModelForm):
    class Meta:
        model=Profile
        fields = ['name', 'type']

class RelDateForm(forms.ModelForm):
    info = forms.CharField(required=False)
    class Meta:
        model = RelativeDate
        fields = ['info','ref','how','offset','relation']

class DateForm(forms.ModelForm):
    info = forms.CharField(required=False)
    class Meta:
        model = Date
        fields = ['estimate','plusminus', 'oxa', 'curve','upper','lower','method','description', 'ref', 'info']

class ReferenceForm(forms.ModelForm):
    class Meta:
        model=Reference
        fields = "__all__"

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactPerson
        fields = '__all__'

class LocationForm(forms.ModelForm):
    class Meta:
        model=Location
        fields = ["name","description","geo","ref"]

class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = ['name','country', 'type', 'elevation','ref','loc','contact']


class LayerForm(forms.ModelForm):
    class Meta:
        model = Layer
        fields = ['name','description','site_use','ref','epoch','checkpoint','related','unit']


class EpochForm(forms.ModelForm):
    upper = forms.IntegerField()
    lower = forms.IntegerField()
    class Meta:
        model = Epoch
        fields = ['name','description','parent','ref','loc', 'upper', 'lower']

class CultureForm(forms.ModelForm):
    class Meta:
        model = Culture
        fields = ['name','description','parent','hominin_group','ref']


class CheckpointForm(forms.ModelForm):
    upper = forms.IntegerField()
    lower = forms.IntegerField()
    class Meta:
        model = Checkpoint
        fields = ['name','description','category','type','ref','loc', 'upper','lower']
