from main.models import models
from main.models import AnalyzedSample, Sample, Project
from main.forms import SampleBatchForm
from django.http import JsonResponse
from django.urls import path
from django.shortcuts import render
from main.tools.generic import get_instance_from_string
import main.tools as tools
from django.db.models import Q
import pandas as pd
import json
from django.contrib.auth.decorators import login_required  # this is for now, make smarter later


def sample_upload(request):
    df = pd.read_csv(request.FILES["file"], sep=",")
    df.drop_duplicates(inplace=True)

    # filter for expected/unexpected columns
    expected = AnalyzedSample.table_columns()
    issues = []
    if dropped := [x for x in df.columns if x not in expected]:
        issues.append(f"Dropped Table Columns: {','.join(dropped)}")
    df = df[[x for x in df.columns if x in expected]]

    # check if sample parents exist
    samples = Sample.objects.values('name')

    if dropped := [x for x in df["Analyzed Sample"] if len(samples.filter(name=x))==0]:
        issues.append(f"Samples not in Database: {','.join(dropped)}")
    df = df[df["Analyzed Sample"].isin(dropped)==False]

    return render(
        request,
        "main/analyzed_samples/analyzedsample-batch-confirm.html",
        {
            "dataframe": df.fillna("").to_html(index=False, classes="table table-striped col-12"),
            "issues": issues,
            "json": df.to_json(),
        },
    )


def save_verified(request):
    df = pd.read_json(request.POST.get("batch-data"))
    df.convert_dtypes()

    # go through the layers
    for i, row in df.iterrows():
        # try if the library already exists
        try:
            object = AnalyzedSample.objects.get(
                library = row['Library'],
                seqrun = row['Sequencing Run'],
            )
        except:
            object = AnalyzedSample(
                sample = Sample.objects.get(name=row['Analyzed Sample']),
                library = row['Library'],
                seqrun = row['Sequencing Run'],
            )
            object.save()
            object.refresh_from_db()
        #set or update
        object.sample = Sample.objects.get(name=row['Analyzed Sample'])
        object.project.add(Project.objects.get(
            namespace=request.session["session_project"]
            )
        )
        object.probes = row['Capture Probe']
        object.save()

    return JsonResponse({"status": True})


urlpatterns = [
    path("upload", sample_upload, name="main_analyzedsample_upload"),
    path("save", save_verified, name="ajax_save_verified_analyzedsamples"),
]