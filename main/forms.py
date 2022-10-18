from django import forms
from .models import Location, Reference

class ReferenceForm(forms.ModelForm):
    class Meta:
        model=Reference
        fields = "__all__"

class LocationForm(forms.ModelForm):
    reflist = forms.CharField(required=False)

    class Meta:
        model=Location
        fields = ["name","geo","reflist"]