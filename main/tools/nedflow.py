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
    fampercent=1
):
    nested_dict = lambda: defaultdict(nested_dict)
    results = nested_dict()
    positive_samples = []
    project = get_project(request)
    sum_per_lib = {}

    try:
        fampercent = float(fampercent)
    except (TypeError, ValueError):
        fampercent = 0

    query = query.filter(analyzedsample__qc_pass=True)

    if only_project:
        query = query.filter(analyzedsample__project=project)

    for entry in query:
        sum_per_lib[entry] = 0
        any_positives = False
        data = json.loads(entry.data)

        for family in data.keys():
            for row in data[family]:
                # filter the entries
                if ancient and "ancientness" in row.keys():
                    try:
                        if ancient not in row["ancientness"]:
                            continue
                    except TypeError:  # empty ancientness column
                        continue

                any_positives = True

                if entry not in results:
                    results[entry] = {}

                try:
                    value = int(row['sum_genus_family'])
                except (ValueError, TypeError, KeyError):
                    value = 0

                # calculate for the display
                sum_per_lib[entry] += value

                if family not in results[entry]:
                    results[entry][family] = {}
                results[entry][family]["raw"] = value

        if any_positives:
            positive_samples.append(entry.analyzedsample)

    # get the maximum sum and compute display values
    try:
        maxsum = max(sum_per_lib.values())
    except ValueError:  # empty sequence
        maxsum = 0

    if maxsum:
        for entry in results:
            for f, v in results[entry].items():
                v["display"] = round(v["raw"] / maxsum, 4) * 100

    # apply the fampercent filter within each library:
    # drop families whose share of that library's total is below the threshold
    if fampercent > 0:
        for entry in list(results.keys()):
            lib_total = sum_per_lib[entry]
            for f in list(results[entry].keys()):
                share = (results[entry][f]["raw"] / lib_total * 100) if lib_total else 0
                if share < fampercent:
                    del results[entry][f]
            if not results[entry]:  # no families left for this library
                del results[entry]

    # build the family list / colors only from families that survived
    families = {f for entry in results for f in results[entry]}

    colors = list(
        zip(
            sorted(families),
            sns.color_palette("husl", len(families)).as_hex(),
        )
    )

    if positives:
        query = query.filter(analyzedsample__in=positive_samples)

    return {
        "quicksand_results": results,
        "object_list": query,
        "colors": colors,
        "ancient": ancient,
        "positives": positives,
        "only_project": only_project,
        "fampercent": fampercent,
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
        fampercent = request.POST.get("fampercent", 1)

        # column: ReadsDeduped
        # filter: ancient, breadth, percentage
        context.update(
            prepare_data(
                request,
                query,
                ancient=ancient,
                positives=positives,
                only_project=only_project,
                fampercent=fampercent
            )
        )
    else:
        context.update(prepare_data(request, query))
        
    
    return render(request, "main/nedflow/nedflow-content.html", context)

urlpatterns = [
    path("get-table/<int:pk>", get_nedflow_tab, name="main_site_getnedflow")
]