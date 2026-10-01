## this file is related to functions handling quicksand report-files
import pandas as pd
import seaborn as sns
from django.contrib import messages
from django.shortcuts import render
from django.urls import path
from django.db.models import Q
from main.tools.generic import get_instance_from_string
from main.tools.projects import get_project
from main.tools.analyzed_samples import update_query_for_negatives, get_libraries
from main.models import NedflowAnalysis, AnalyzedSample, Site
import re
import json
from collections import defaultdict


def handle_nedflow_report(request, file):
    """
    Handle the uploaded quicksand report. In the report a "RG" together with the sequencing run link to one 'Analyzed Sample' and can be linked.
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
                "type": "nedflow_upload",
            },
        )

    df = pd.read_csv(file, sep="\t")

    # input verification
    runid = request.POST.get("sequencing", False)
    if not runid:
        return return_error("Sequencing ID is missing")

    lane = request.POST.get("lane", False)

    version = request.POST.get("version", False)
    version_format_matches = bool(re.match("v[0-9]+(\.[0-9]+)*", version))

    if not all([version, version_format_matches]):
        return return_error("NedFlow version missing or wrong format")

    ## Import the report now
    not_found = []
    imported = []

    for library, report in df.groupby("library"):
        try:
            if library.startswith("Lib"):
                try:
                    analyzed_sample = AnalyzedSample.objects.get(
                        library=library, seqrun=runid, lane=lane
                    )
                # could be a reamp library
                except AnalyzedSample.DoesNotExist:
                    analyzed_sample = AnalyzedSample.objects.get(
                        reamp_library=library, seqrun=runid, lane=lane
                    )
            elif library.startswith("Cap"):
                analyzed_sample = AnalyzedSample.objects.get(
                    capture=library, seqrun=runid, lane=lane
                )
            elif library.startswith("ERR"): # published data: ENA ID
                analyzed_sample = AnalyzedSample.objects.get(
                    capture=library, seqrun=runid, lane=lane
                )
            else: # now this is a random library identifier
                analyzed_sample = AnalyzedSample.objects.get(
                    library=library, seqrun=runid, lane=lane
                )
            # prepare the data for saving
            data = {}

            for i, tmp in report.groupby("family", as_index=False):
                data[i] = list(json.loads(tmp.to_json(orient="index")).values())

            # get or create the quicksand-analysis object
            # analyzed_sample and version are unique together
            nf, created = NedflowAnalysis.objects.get_or_create(
                analyzedsample=analyzed_sample, version=version
            )
            nf.data = json.dumps(data)
            nf.save()
            imported.append(library)

        except:  # doesnt exist
            not_found.append(library)

    if len(not_found) > 0:
        messages.add_message(
            request,
            messages.WARNING,
            f"{', '.join(not_found)}: Libraries not found in database, ignored for upload",
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
            "type": "nedflow_upload",
        },
    )


def prepare_data(
    request,
    query,
    ancient='++',
    positives=False,
    only_project=True,
):

    families = []  # for the colors
    nested_dict = lambda: defaultdict(nested_dict)
    results = nested_dict()
    positive_samples = []
    project = get_project(request)
    sum_per_lib = {}

    query = query.filter(analyzedsample__qc_pass=True)

    if only_project:
        query = query.filter(analyzedsample__project=project)

    for entry in query:
        sum_per_lib[entry] = 0
        any_positives = False
        data = json.loads(entry.data)
        for family in data.keys():
            for row in data[family]:
                # now filters the entries
                if ancient and "ancientness" in row.keys():
                    try:
                        if not ancient in row["ancientness"]:
                            continue
                    except TypeError: #empty ancientness column
                        continue

                any_positives = True

                if not entry in results:
                    results[entry] = {}

                try:
                    value = int(row['sum_genus_family'])
                except:
                    value = 0

                # calculate for the display
                sum_per_lib[entry] = sum_per_lib[entry] + value

                if not family in results[entry]:
                    results[entry][family] = {}
                results[entry][family]["raw"] = value
                families.append(family)

        if any_positives:
            positive_samples.append(entry.analyzedsample)

    # get the maximum sum
    try:
        maxsum = max([x for x in sum_per_lib.values()])
        for entry in results.keys():
            for f, v in results[entry].items():
                results[entry][f]["display"] = round(v["raw"] / maxsum, 4) * 100
    except ValueError:  # empty sequence
        maxsum = 0

    families = set(families)

    colors = [
        (k, v)
        for k, v in zip(
            [x for x in sorted(families)],
            sns.color_palette("husl", len(families)).as_hex(),
        )
    ]

    if positives:
        query = query.filter(analyzedsample__in=positive_samples)

    return {
        "quicksand_results": results,
        "object_list": query,
        "colors": colors,
        "ancient": ancient,
        "positives": positives,
        "only_project": only_project,
    }

def get_nedflow_tab(request, pk):
    """
    In the DNA Tab, render the quicksand table and form
    """
    site = Site.objects.get(pk=int(pk))
    context = {"object": site}

    # first, get the objects
    analyzed_samples = get_libraries(request, site.pk, return_query=True, unset=False)

    #order by analyzed sample to match the order of the table above the quicksand tab
    query = NedflowAnalysis.objects.filter(analyzedsample__in=analyzed_samples).order_by('analyzedsample')


    # Additional filters -> TODO:Adjust to NedFlow
    if request.method == "POST":
        ancient = request.POST.get("ancient")
        positives = "on" == request.POST.get("positives", "")
        only_project = "on" == request.POST.get("only_project", "")

        # column: ReadsDeduped
        # filter: ancient, breadth, percentage
        context.update(
            prepare_data(
                request,
                query,
                ancient=ancient,
                positives=positives,
                only_project=only_project,
            )
        )
    else:
        context.update(prepare_data(request, query))
        
    
    return render(request, "main/nedflow/nedflow-content.html", context)

urlpatterns = [
    path("get-table/<int:pk>", get_nedflow_tab, name="main_site_getnedflow")
]