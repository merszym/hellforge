from main.models import models
from main.models import AnalyzedSample, Sample, Project, SampleBatch
from django.http import JsonResponse, HttpResponse
from django.urls import path
from django import forms
from django.shortcuts import render
from main.tools.generic import get_instance_from_string
import main.tools as tools
from django.db.models import Q
import pandas as pd
import json
from django.contrib.auth.decorators import (
    login_required,
)  # this is for now, make smarter later
from django.contrib import messages


class AnalyzedSampleForm(forms.ModelForm):
    class Meta:
        model = AnalyzedSample
        fields = ["seqrun", "seqpool", "lane"]


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
        object.tags = row["Tag"]
        object.project.add(
            Project.objects.get(namespace=request.session["session_project"])
        )
        object.probes = row["Capture Probe"]
        object.save()

    from main.tools.site import get_site_samplebatch_tab

    return get_site_samplebatch_tab(request, batch.pk)


def tags_update(request, pk):
    object = AnalyzedSample.objects.get(pk=pk)
    val = request.POST.get("tags", None)

    object.tags = val
    object.save()

    # finally, return the modal
    messages.add_message(
        request,
        messages.SUCCESS,
        f"Update of tag successful",
    )

    request.GET._mutable = True
    request.GET.update({"object": f"{object.model}_{object.pk}", "type": "tags"})

    from main.ajax import get_modal

    return get_modal(request)


def seqrun_update(request, pk):
    object = AnalyzedSample.objects.get(pk=pk)
    # in case we want to update all
    old_run = object.seqrun
    old_lane = object.lane
    old_pool = object.seqpool

    form = AnalyzedSampleForm(request.POST, instance=object)

    if form.is_valid():
        form.save()

    if request.GET.get("all", "no") == "yes":
        libs = AnalyzedSample.objects.filter(
            Q(seqrun=old_run)
            & Q(seqpool=old_pool)
            & Q(lane=old_lane)
            & Q(sample__site=object.sample.site)
        )
        for lib in libs:
            form = AnalyzedSampleForm(request.POST, instance=lib)
            if form.is_valid():
                form.save()

    # finally, return the modal
    messages.add_message(
        request,
        messages.SUCCESS,
        f"Update of Seqrun(s) successful",
    )

    request.GET._mutable = True
    request.GET.update({"object": f"{object.model}_{object.pk}", "type": "edit_seqrun"})

    from main.ajax import get_modal

    return get_modal(request)


def qc_toggle(request, pk):
    object = AnalyzedSample.objects.get(pk=pk)

    object.qc_pass = object.qc_pass == False
    object.save()

    if object.qc_pass:  # needs to get removed
        return HttpResponse("<span style='color:green; cursor:pointer;'>Pass</span>")
    else:
        return HttpResponse("<span style='color:red; cursor:pointer;'>Fail</span>")


urlpatterns = [
    path("save", save_verified, name="ajax_save_verified_analyzedsamples"),
    path("<int:pk>/update-tags", tags_update, name="main_analyzedsample_tagupdate"),
    path(
        "<int:pk>/update-seqrun", seqrun_update, name="main_analyzedsample_seqrunupdate"
    ),
    path("<int:pk>/update-qc", qc_toggle, name="main_analyzedsample_qctoggle"),
]
