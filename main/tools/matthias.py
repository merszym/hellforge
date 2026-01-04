
from main.models import AnalyzedSample, HumanDiagnosticPositions, Site
from main.tools.generic import get_instance_from_string
from main.tools.projects import get_project
from main.tools.analyzed_samples import get_libraries

import pandas as pd
import seaborn as sns
import json

from django.shortcuts import render
from django.contrib import messages
from django.urls import path
from main.tools.analyzed_samples import update_query_for_negatives
from django.db.models import Q
from collections import defaultdict



def handle_file_upload(request, file):
    """
    Handle the uploaded summary script. In the script a CapLibID/IndexLibID together with the sequencing run links to one 'Analyzed Sample' and can be linked.
    Store all the data in one JSON (for now)
    """

    def return_error(error):
        messages.add_message(
            request,
            messages.ERROR,
            f"{error}",
        )
        return render(
            request,
            "main/modals/site_modal.html",
            {
                "object": get_instance_from_string(request.POST.get("object")),
                "type": "matthias_upload",
            },
        )

    df = pd.read_csv(file, sep="\t", index_col=False)
    df = df[[x for x in df.columns if x.startswith('Unnamed')==False]].copy()

    # input verification
    runid = request.POST.get("sequencing", False)
    
    if not runid:
        return return_error("Sequencing ID is missing")

    seqpool = request.POST.get("seqpool", False)

    version = request.POST.get("version", False)

    ## Import the report now
    not_found = []
    imported = []

    for i, data in df.iterrows():
        try:
            if data["CapLibIDCoreDB"]:
                analyzed_sample = AnalyzedSample.objects.get(
                    capture=data["CapLibIDCoreDB"], seqrun=runid, seqpool=seqpool
                )
            elif data["IndexLibIDCoreDB"]:
                try:
                    analyzed_sample = AnalyzedSample.objects.get(
                        library=data["IndexLibIDCoreDB"], seqrun=runid, seqpool=seqpool
                    )
                except AnalyzedSample.DoesNotExist:
                    analyzed_sample = AnalyzedSample.objects.get(
                        reamp_library=data["IndexLibIDCoreDB"], seqrun=runid, seqpool=seqpool
                    )
            else:
                raise TypeError
            # prepare the data for saving
            entry = json.loads(data.to_json(orient="index"))
            
            imported.append(data["CapLibIDCoreDB"])
            
            # get or create the quicksand-analysis object
            # analyzed_sample and version are unique together
            matthias, created = HumanDiagnosticPositions.objects.get_or_create(
                analyzedsample=analyzed_sample, version=version
            )
            matthias.data = json.dumps(entry)
            matthias.save()
            
        except:  # doesnt exist
            not_found.append(data["CapLibIDCoreDB"])

    if len(not_found) > 0:
        messages.add_message(
            request,
            messages.WARNING,
            f"{len(not_found)} Libraries not found in database, ignored for upload",
        )

    if len(imported) > 0:
        messages.add_message(
            request,
            messages.SUCCESS,
            f"{', '.join(imported)}: Upload successful",
        )

    return render(
        request,
        "main/modals/site_modal.html",
        {
            "object": get_instance_from_string(request.POST.get("object")),
            "type": "matthias_upload",
        },
    )


def prepare_data(
    request,
    query,
    ancient=True,
    positives=False,
    extended=False
):

    lineages = []  # for the colors
    nested_dict = lambda: defaultdict(nested_dict)
    positive_samples = []
    results = nested_dict()
    project = get_project(request)

    for entry in query:
        data = json.loads(entry.data)
        results[entry] = data
        if data["Ancient"]=="++":
            positive_samples.append(entry)
        
        if ancient:
            lineages.extend([x for x in data.keys() if x.endswith('deam')]) 
        else:
            lineages.extend([x for x in data.keys() if x.endswith('support')])

    lineages = sorted(list(set(lineages)), key=lambda x: ["H","N","N-HST","HST","D","D-S","S"].index(x.split("_")[0]) )

    colors = [
        (k, v)
        for k, v in zip(
            lineages,
            sns.color_palette("husl", len(lineages)).as_hex(),
        )
    ]

    if positives:
        query = positive_samples
    
    return {
        "results": results,
        "object_list": query,
        "lineages": colors,
        "ancient": ancient,
        "positives": positives,
        "extended": extended,
    }


def get_matthias_tab(request, pk):
    site = Site.objects.get(pk=int(pk))
    context = {"object": site}

    # first, get the objects
    analyzed_samples = get_libraries(request, site.pk, return_query=True, unset=False)

    query = HumanDiagnosticPositions.objects.filter(analyzedsample__in=analyzed_samples).order_by('analyzedsample')

    if request.method == "POST":
        ancient = "on" == request.POST.get("ancient", "")
        positives = "on" == request.POST.get("positives", "")
        extended = "on" == request.POST.get("extended", "")

        context.update(
            prepare_data(
                request,
                query,
                ancient=ancient,
                positives=positives,
                extended=extended
            )
        )
    else:
        context.update(prepare_data(request, query))

    return render(request, "main/matthias/matthias-content.html", context)


urlpatterns = [
    path("get-table/<int:pk>", get_matthias_tab, name="main_site_getmatthias")
]