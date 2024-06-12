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
    SampleBatch,
)


class SampleBatchForm(forms.ModelForm):
    class Meta:
        model = SampleBatch
        fields = ["site", "name", "sampled_by", "year_of_arrival"]


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["name", "type"]


class DateForm(forms.ModelForm):
    info = forms.CharField(required=False)

    class Meta:
        model = Date
        fields = [
            "estimate",
            "plusminus",
            "sigma",
            "oxa",
            "curve",
            "upper",
            "lower",
            "method",
            "description",
            "ref",
            "info",
        ]


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
    lat = forms.FloatField(required=False)
    long = forms.FloatField(required=False)

    class Meta:
        model = Site
        fields = [
            "name",
            "site",
            "coredb_id",
            "country",
            "type",
            "elevation",
            "lat",
            "long",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].initial = ""


class EpochForm(forms.ModelForm):
    upper = forms.IntegerField()
    lower = forms.IntegerField()

    class Meta:
        model = Epoch
        fields = ["name", "upper", "lower"]


class CultureForm(forms.ModelForm):
    class Meta:
        model = Culture
        fields = ["name", "hominin_group", "culture"]
