## this file is related to functions handling quicksand report-files
import pandas as pd
import seaborn as sns
from django.contrib import messages
from django.shortcuts import render
from main.tools.generic import get_instance_from_string
from main.models import QuicksandAnalysis, AnalyzedSample
import re
import json


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

    version = request.POST.get("version", False)
    version_format_matches = bool(re.match("v[0-9]+(\.[0-9]+)*", version))

    if not all([version, version_format_matches]):
        return return_error("quicksand version missing or wrong format")

    ## Import the report now
    not_found = []
    imported = []

    for library, report in df.groupby("RG"):
        try:
            analyzed_sample = AnalyzedSample.objects.get(library=library, seqrun=runid)

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


def prepare_data(query, column="ReadsDeduped", filter="aa_p0.5_b0.5", mode="relative"):
    print(query)

    return query
