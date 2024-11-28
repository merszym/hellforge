## this file is related to functions handling quicksand report-files
import pandas as pd
import seaborn as sns
from django.contrib import messages
from django.shortcuts import render
from django.urls import path
from django.db.models import Q
from main.tools.generic import get_instance_from_string
from main.tools.projects import get_project
from main.tools.analyzed_samples import update_query_for_negatives
from main.models import QuicksandAnalysis, AnalyzedSample, Site
import re
import json
from collections import defaultdict


def handle_quicksand_report(request, file):
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
                "type": "quicksand_upload",
            },
        )

    df = pd.read_csv(file, sep="\t")

    # input verification
    runid = request.POST.get("sequencing", False)
    if not runid:
        return return_error("Sequencing ID is missing")

    seqpool = request.POST.get("seqpool", False)

    version = request.POST.get("version", False)
    version_format_matches = bool(re.match("v[0-9]+(\.[0-9]+)*", version))

    if not all([version, version_format_matches]):
        return return_error("quicksand version missing or wrong format")

    ## Import the report now
    not_found = []
    imported = []

    for library, report in df.groupby("RG"):
        try:
            if library.startswith("Lib"):
                analyzed_sample = AnalyzedSample.objects.get(
                    library=library, seqrun=runid, seqpool=seqpool
                )
            elif library.startswith("Cap"):
                analyzed_sample = AnalyzedSample.objects.get(
                    capture=library, seqrun=runid, seqpool=seqpool
                )
            else:
                raise TypeError
            # prepare the data for saving
            data = {}

            for i, tmp in report.groupby("Family", as_index=False):
                data[i] = list(json.loads(tmp.to_json(orient="index")).values())

            # get or create the quicksand-analysis object
            # analyzed_sample and version are unique together
            qs, created = QuicksandAnalysis.objects.get_or_create(
                analyzedsample=analyzed_sample, version=version
            )
            qs.data = json.dumps(data)
            qs.save()
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
            "type": "quicksand_upload",
        },
    )


def prepare_data(
    request,
    query,
    column="ReadsDeduped",
    ancient=True,
    mode="absolute",
    percentage=0.5,
    breadth=0.5,
    positives=False,
    only_project=True,
    controls=False,
    tableview=False
):

    families = []  # for the colors
    nested_dict = lambda: defaultdict(nested_dict)
    results = nested_dict()
    positive_samples = []
    project = get_project(request)
    sum_per_lib = {}

    if only_project:
        query = query.filter(analyzedsample__project=project)

    if controls == False:
        query = query.exclude(analyzedsample__sample__isnull=True)

    for entry in query:
        sum_per_lib[entry] = 0
        any_positives = False
        data = json.loads(entry.data)
        for family in data.keys():
            for row in data[family]:
                # now filters the entries
                if ancient and "Ancientness" in row.keys():
                    if not row["Ancientness"] == "++":
                        continue
                if percentage > 0 and "FamPercentage" in row.keys():
                    if not row["FamPercentage"] >= percentage:
                        continue
                if breadth > 0 and "ProportionExpectedBreadth" in row.keys():
                    if row["ProportionExpectedBreadth"] == None:
                        continue
                    if not row["ProportionExpectedBreadth"] >= breadth:
                        continue

                any_positives = True

                if not entry in results:
                    results[entry] = {}

                # TODO: if entries are fixed or rerun, there might be multiple entries here... fix later
                try:
                    value = int(row[column])
                except:
                    value = 0

                # calculate for the display
                sum_per_lib[entry] = sum_per_lib[entry] + value

                if not family in results[entry]:
                    results[entry][family] = {}
                results[entry][family]["raw"] = value
                families.append(family)

        if mode == "relative":
            for f, v in results[entry].items():
                results[entry][f]["display"] = (
                    round(v["raw"] / sum_per_lib[entry], 4) * 100
                )
                results[entry][f]["raw"] = results[entry][f]["display"]

        if any_positives:
            positive_samples.append(entry.analyzedsample)

    if mode == "absolute":
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
        "mode": mode,
        "column": column,
        "percentage": percentage,
        "breadth": breadth,
        "ancient": ancient,
        "positives": positives,
        "only_project": only_project,
        "controls": controls,
        "tableview": tableview
    }


def get_data_for_export(data, quickv, percentage=0.5, breadth=0.5):
    export = {
        "quicksand version": quickv,
        "ReadsRaw": 0,
        "ReadsLengthfiltered": 0,
        "ReadsIdentified": 0,
        "ReadsMapped": 0,
        "ReadsDeduped": 0,
        "DuplicationRate": 0,
        "ReadsBedfiltered": 0,
        "SeqsInAncientTaxa": 0,
        "Ancient": "-",
        "AncientTaxa": [],
        "OtherTaxa": [],
        "Subsitutions": [],
    }

    if len(data) == 0:
        return export

    data = json.loads(data)
    for family in data:
        entry = data[family][0]

        # overwrite, but its the same for all
        export["ReadsRaw"] = entry["ReadsRaw"]
        export["ReadsLengthfiltered"] = entry["ReadsLengthfiltered"]

        # check filters:
        if not entry["FamPercentage"] >= percentage:
            continue
        if "ProportionExpectedBreadth" in entry.keys():
            if entry["ProportionExpectedBreadth"] == None:
                continue
            if not entry["ProportionExpectedBreadth"] >= breadth:
                continue

        # Add
        export["ReadsIdentified"] = export["ReadsIdentified"] + entry["ReadsExtracted"]
        export["ReadsMapped"] = export["ReadsMapped"] + entry["ReadsMapped"]
        export["ReadsDeduped"] = export["ReadsDeduped"] + entry["ReadsDeduped"]
        try:
            export["DuplicationRate"] = round(
                export["ReadsMapped"] / export["ReadsDeduped"], 2
            )
        except:
            export["DuplicationRate"] = 0
        try:
            export["ReadsBedfiltered"] = export["ReadsBedfiltered"] + int(
                entry["ReadsBedfiltered"]
            )
        except:
            # some have '-', which should be ignored
            pass
        if entry["Ancientness"] == "+":
            # update the export only if not already marked as ancient
            if export["Ancient"] == "-":
                export["Ancient"] = "+"
        if entry["Ancientness"] == "++":
            export["SeqsInAncientTaxa"] = (
                export["SeqsInAncientTaxa"] + entry["ReadsDeduped"]
            )
            export["Ancient"] = "++"
            export["AncientTaxa"].append(
                f"{family}({entry['ReadsDeduped']}[{entry['FamPercentage']}%])"
            )
        if entry["Ancientness"] in ["+", "-"]:
            export["OtherTaxa"].append(
                f"{family}({entry['ReadsDeduped']}[{entry['FamPercentage']}%])"
            )

        # reformat the subsitutions
        deam5 = (
            entry["Deam5(95ci)"]
            .replace(" ", "")
            .replace(",", "-")
            .replace("(", "[")
            .replace(")", "]")
        )
        deam3 = (
            entry["Deam3(95ci)"]
            .replace(" ", "")
            .replace(",", "-")
            .replace("(", "[")
            .replace(")", "]")
        )

        export["Subsitutions"].append(f"{family}({deam5},{deam3})")

    # now remove the lists
    export["AncientTaxa"] = (
        " ".join(export["AncientTaxa"]) if len(export["AncientTaxa"]) > 0 else "-"
    )
    export["OtherTaxa"] = (
        " ".join(export["OtherTaxa"]) if len(export["OtherTaxa"]) > 0 else "-"
    )
    export["Subsitutions"] = (
        " ".join(export["Subsitutions"]) if len(export["Subsitutions"]) > 0 else "-"
    )

    return export


def get_quicksand_tab(request, pk):
    """
    In the DNA Tab, render the quicksand table and form
    """
    site = Site.objects.get(pk=int(pk))
    context = {"object": site}

    # first, get the objects
    analyzed_samples = update_query_for_negatives(
        AnalyzedSample.objects.filter(Q(sample__site=site) & Q(qc_pass=True))
    )
    query = QuicksandAnalysis.objects.filter(analyzedsample__in=analyzed_samples)

    if request.method == "POST":
        if prset := request.POST.get("probe", False):
            if prset != "all":
                if prset == "AA163":  # get all the human mt probesets
                    query = query.filter(analyzedsample__probes__in=["AA163", "AA22"])
                else:
                    query = query.filter(analyzedsample__probes=prset)
            context.update({"probe": prset})

        mode = request.POST.get("mode", "absolute")
        column = request.POST.get("column", "ReadsDeduped")
        percentage = float(request.POST.get("percentage", 0.5))
        breadth = float(request.POST.get("breadth", 0.5))
        ancient = "on" == request.POST.get("ancient", "")
        positives = "on" == request.POST.get("positives", "")
        only_project = "on" == request.POST.get("only_project", "")
        controls = "on" == request.POST.get("controls", "")
        tableview = "on" == request.POST.get("tableview", "")

        # column: ReadsDeduped
        # mode: relative,absolute
        # filter: ancient, breadth, percentage

        context.update(
            prepare_data(
                request,
                query,
                column=column,
                percentage=percentage,
                breadth=breadth,
                mode=mode,
                ancient=ancient,
                positives=positives,
                only_project=only_project,
                controls=controls,
                tableview=tableview
            )
        )
    else:
        query = query.filter(analyzedsample__probes="AA75")
        context.update({"probe": "AA75"})
        context.update(prepare_data(request, query))
    
    return render(request, "main/quicksand/quicksand-content.html", context)


urlpatterns = [
    path("get-table/<int:pk>", get_quicksand_tab, name="main_site_getquicksand")
]