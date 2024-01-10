from main.models import models
from main.models import AnalyzedSample, Sample, Project, SampleBatch
from django.http import JsonResponse
from django.urls import path
from django.shortcuts import render
from main.tools.generic import get_instance_from_string
import main.tools as tools
from django.db.models import Q
import pandas as pd
import json
from django.contrib.auth.decorators import (
    login_required,
)  # this is for now, make smarter later


def handle_library_file(request, file):
    df = pd.read_csv(file, sep=",")
    df.drop_duplicates(inplace=True)

    batch = SampleBatch.objects.get(pk=int(request.GET.get("batch")))
    # filter for expected/unexpected columns
    expected = AnalyzedSample.table_columns()
    issues = []
    if dropped := [x for x in df.columns if x not in expected]:
        issues.append(f"Dropped Table Columns: {','.join(dropped)}")
    df = df[[x for x in df.columns if x in expected]]

    # check if sample parents exist
    samples = Sample.objects.values("name")

    if dropped := [
        x for x in df["Analyzed Sample"] if len(samples.filter(name=x)) == 0
    ]:
        issues.append(f"Samples not in Database: {','.join(dropped)}")
    df = df[df["Analyzed Sample"].isin(dropped) == False]

    return render(
        request,
        "main/modals/sample_modal.html",
        {
            "type": "libraries_confirm",
            "dataframe": df.fillna("").to_html(
                index=False, classes="table table-striped col-12"
            ),
            "issues": issues,
            "json": df.to_json(),
            "batch": batch,
        },
    )


def save_verified(request):
    df = pd.read_json(request.POST.get("batch-data"))
    df.convert_dtypes()

    batch = SampleBatch.objects.get(pk=int(request.GET.get("batch")))

    # go through the layers
    for i, row in df.iterrows():
        # try if the library already exists
        try:
            object = AnalyzedSample.objects.get(
                library=row["Library"],
                seqrun=row["Sequencing Run"],
            )
        except:
            object = AnalyzedSample(
                sample=Sample.objects.get(name=row["Analyzed Sample"]),
                library=row["Library"],
                seqrun=row["Sequencing Run"],
            )
            object.save()
            object.refresh_from_db()
        # set or update
        object.sample = Sample.objects.get(name=row["Analyzed Sample"])
        object.project.add(
            Project.objects.get(namespace=request.session["session_project"])
        )
        object.probes = row["Capture Probe"]
        object.save()

    from main.tools.site import get_site_samplebatch_tab

    return get_site_samplebatch_tab(request, object=batch)


urlpatterns = [
    path("save", save_verified, name="ajax_save_verified_analyzedsamples"),
]
