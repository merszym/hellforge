from django import forms
from .models import Location, Reference, Site, Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model=Profile
        fields = ['name', 'type']

class ReferenceForm(forms.ModelForm):
    class Meta:
        model=Reference
        fields = "__all__"

class LocationForm(forms.ModelForm):
    reflist = forms.CharField(required=False)

    class Meta:
        model=Location
        fields = ["name","geo","reflist"]

class SiteForm(forms.ModelForm):
    reflist = forms.CharField(required=False)
    loclist = forms.CharField(required=False)

    class Meta:
        model = Site
        fields = ['name', 'type', 'elevation','reflist','loclist']

