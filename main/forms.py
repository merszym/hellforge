from django import forms
from .models import Location, Reference, Site, Profile, Layer, Culture, Date, Epoch

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
        fields = ['name', 'type', 'elevation','description','reflist','loclist']


class LayerForm(forms.ModelForm):
    reflist = forms.CharField(required=False)

    class Meta:
        model = Layer
        fields = ['name','description','reflist']


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
        fields = ['name','description','reflist','loclist', 'datelist']