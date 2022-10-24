from django import forms
from .models import Location, Reference, Site, Profile, Layer, Culture, Date, Epoch, Checkpoint

class ProfileForm(forms.ModelForm):
    class Meta:
        model=Profile
        fields = ['name', 'type']

class DateForm(forms.ModelForm):
    class Meta:
        model = Date
        fields = ['upper','lower','method','description']

class DateUpdateForm(forms.ModelForm):
    reflist = forms.CharField(required=False)

    class Meta:
        model = Date
        fields = ['upper','lower','method','description', 'reflist']

class ReferenceForm(forms.ModelForm):
    class Meta:
        model=Reference
        fields = "__all__"

class LocationForm(forms.ModelForm):
    reflist = forms.CharField(required=False)

    class Meta:
        model=Location
        fields = ["name","description","geo","reflist"]

class SiteForm(forms.ModelForm):
    reflist = forms.CharField(required=False)
    loclist = forms.CharField(required=False)

    class Meta:
        model = Site
        fields = ['name','country', 'type', 'elevation','description','reflist','loclist']


class LayerForm(forms.ModelForm):
    reflist = forms.CharField(required=False)
    culturelist = forms.CharField(required=False)
    datelist = forms.CharField(required=False)
    epochlist = forms.CharField(required=False)
    checkpointlist = forms.CharField(required=False)

    class Meta:
        model = Layer
        fields = ['name','description','site_use','reflist','culturelist','epochlist','checkpointlist','datelist']


class EpochForm(forms.ModelForm):
    reflist = forms.CharField(required=False)
    loclist = forms.CharField(required=False)
    datelist = forms.CharField(required=False)

    class Meta:
        model = Epoch
        fields = ['name','description','reflist','loclist', 'datelist']

class CultureForm(forms.ModelForm):
    reflist = forms.CharField(required=False)
    loclist = forms.CharField(required=False)
    datelist = forms.CharField(required=False)

    class Meta:
        model = Culture
        fields = ['name','description','hominin_group','reflist','loclist', 'datelist']


class CheckpointForm(forms.ModelForm):
    reflist = forms.CharField(required=False)
    loclist = forms.CharField(required=False)
    datelist = forms.CharField(required=False)

    class Meta:
        model = Checkpoint
        fields = ['name','description','category','type','reflist','loclist', 'datelist']