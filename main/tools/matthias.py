
from main.models import AnalyzedSample, HumanDiagnosticPositions, Site
from main.tools.generic import get_instance_from_string
from main.tools.projects import get_project

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

    print(df)

    for i, data in df.iterrows():
        try:
            if data["CapLibIDCoreDB"]:
                analyzed_sample = AnalyzedSample.objects.get(
                    capture=data["CapLibIDCoreDB"], seqrun=runid, seqpool=seqpool
                )
            elif data["IndexLibIDCoreDB"]:
                analyzed_sample = AnalyzedSample.objects.get(
                    library=data["IndexLibIDCoreDB"], seqrun=runid, seqpool=seqpool
                )
            else:
                raise TypeError
            print(analyzed_sample)
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
    only_project=True,
    controls=False,
    extended=False
):

    lineages = []  # for the colors
    nested_dict = lambda: defaultdict(nested_dict)
    positive_samples = []
    results = nested_dict()
    project = get_project(request)

    if only_project:
        query = query.filter(analyzedsample__project=project)

    if controls == False:
        query = query.exclude(analyzedsample__sample__isnull=True)

    for entry in query:
        data = json.loads(entry.data)
        results[entry] = data
        if data["Ancient"]=="++":
            positive_samples.append(entry)
        
        if ancient:
            lineages.extend([x for x in data.keys() if x.endswith('deam')]) 
        else:
            lineages.extend([x for x in data.keys() if x.endswith('support')])

    lineages = sorted(list(set(lineages)), key=lambda x: ["H","N","D",'S'].index(x[0]) )

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
        "only_project": only_project,
        "controls": controls,
    }


def get_matthias_tab(request, pk):
    site = Site.objects.get(pk=int(pk))
    context = {"object": site}

        # first, get the objects
    analyzed_samples = update_query_for_negatives(
        AnalyzedSample.objects.filter(Q(sample__site=site) & Q(qc_pass=True))
    )
    query = HumanDiagnosticPositions.objects.filter(analyzedsample__in=analyzed_samples)

    if request.method == "POST":
        if prset := request.POST.get("probe", False):
            if prset != "all":
                if prset == "AA163":  # get all the human mt probesets
                    query = query.filter(analyzedsample__probes__in=["AA163", "AA22"])
                else:
                    query = query.filter(analyzedsample__probes=prset)
            context.update({"probe": prset})

        ancient = "on" == request.POST.get("ancient", "")
        positives = "on" == request.POST.get("positives", "")
        only_project = "on" == request.POST.get("only_project", "")
        controls = "on" == request.POST.get("controls", "")
        extended = "on" == request.POST.get("extended", "")

        context.update(
            prepare_data(
                request,
                query,
                ancient=ancient,
                positives=positives,
                only_project=only_project,
                controls=controls,
                extended=extended
            )
        )
    else:
        query = query.filter(analyzedsample__probes__in=["AA163", "AA22"])
        context.update({"probe": "AA163"})
        context.update(prepare_data(request, query))

    return render(request, "main/matthias/matthias-content.html", context)


urlpatterns = [
    path("get-table/<int:pk>", get_matthias_tab, name="main_site_getmatthias")
]