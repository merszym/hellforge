from django import forms
from .models import (
    Reference,
    Site,
    Profile,
    Culture,
    Date,
    Epoch,
    Person,
    Synonym,
)


class SynonymForm(forms.ModelForm):
    class Meta:
        model = Synonym
        fields = "__all__"


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["name", "type"]


class DateForm(forms.ModelForm):
    info = forms.CharField(required=False)

    class Meta:
        model = Date
        fields = ["estimate", "plusminus", "oxa", "curve", "upper", "lower", "method", "description", "ref", "info"]


class ReferenceForm(forms.ModelForm):
    class Meta:
        model = Reference
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": "form-input"})


class ContactForm(forms.ModelForm):
    class Meta:
        model = Person
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].initial = ""
            self.fields[field].widget.attrs.update({"class": "form-input"})


class SiteForm(forms.ModelForm):
    geo = forms.JSONField(required=False)

    class Meta:
        model = Site
        fields = ["name", "coredb_id", "country", "type", "elevation", "geo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].initial = ""


class EpochForm(forms.ModelForm):
    upper = forms.IntegerField()
    lower = forms.IntegerField()

    class Meta:
        model = Epoch
        fields = ["name", "description", "parent", "ref", "upper", "lower"]


class CultureForm(forms.ModelForm):
    class Meta:
        model = Culture
        fields = ["name", "hominin_group"]
