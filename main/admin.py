import json
from django import forms
from django.contrib import admin
from .models import *

admin.site.register(Reference)
admin.site.register(Project)
admin.site.register(Date)
admin.site.register(Culture)
admin.site.register(Epoch)
admin.site.register(Location)
admin.site.register(Site)
admin.site.register(Profile)
admin.site.register(Layer)
admin.site.register(Sample)
admin.site.register(Person)
admin.site.register(Affiliation)
admin.site.register(Author)
admin.site.register(Image)
admin.site.register(Gallery)
admin.site.register(DatingMethod)
admin.site.register(Synonym)
admin.site.register(Description)
admin.site.register(SampleBatch)
admin.site.register(AnalyzedSample)
admin.site.register(ProjectTag)
admin.site.register(ProbeTranslationTable)
admin.site.register(Connection)
admin.site.register(FaunalResults)
admin.site.register(SpeciesTranslation)
admin.site.register(ImageAnnotation)
admin.site.register(LayerAnalysis)
admin.site.register(Taxonomy)
admin.site.register(QuicksandAnalysis)
admin.site.register(FamilyAnalysis)


# the labels-file (tsv: Name, Species, Haplogroup, ...) of a family is uploaded here and stored as JSON
class CladeReferenceForm(forms.ModelForm):
    labels_file = forms.FileField(required=False, help_text="Labels file (tsv). Replaces the labels data")
    # plain text instead of the strict JSON-field: trailing commas are fine
    color_palette = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 12, "cols": 60}),
        help_text='{"Crocuta crocuta (A1)": "#1f77b4", "Proteles cristatus": "#98df8a", ...}',
    )

    class Meta:
        model = CladeReference
        fields = ["family", "version", "labels_file", "data", "color_palette"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.color_palette:
            self.initial["color_palette"] = json.dumps(self.instance.color_palette, indent=4)

    def clean_color_palette(self):
        import re

        text = self.cleaned_data.get("color_palette", "").strip()
        if not text:
            return None
        try:
            palette = json.loads(re.sub(r",\s*}", "}", text))  # without the trailing comma
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f"Not readable: {e}")
        if not isinstance(palette, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in palette.items()):
            raise forms.ValidationError('Expected {"clade": "color", ...}')
        return {k.strip(): v.strip() for k, v in palette.items()}

    def clean(self):
        cleaned = super().clean()
        file = cleaned.get("labels_file")
        if file:
            import pandas as pd

            table = pd.read_csv(file, sep="\t", dtype=str).fillna("")
            missing = {"Name", "Species", "Haplogroup"} - set(table.columns)
            if missing:
                raise forms.ValidationError(f"Columns missing in the labels file: {', '.join(sorted(missing))}")
            cleaned["data"] = table.to_dict(orient="records")
        elif not cleaned.get("data"):
            raise forms.ValidationError("Upload a labels file")
        return cleaned


@admin.register(CladeReference)
class CladeReferenceAdmin(admin.ModelAdmin):
    form = CladeReferenceForm
    list_display = ["family", "version"]
