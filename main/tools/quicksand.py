## this file is related to functions handling quicksand report-files
import pandas as pd
import seaborn as sns
from django.contrib import messages
from django.shortcuts import render
from main.tools.generic import get_instance_from_string
from main.models import QuicksandAnalysis, AnalyzedSample


def handle_quicksand_report(request, file):
    """
    Handle the uploaded quicksand report. In the report a "RG" together with the sequencing run link to one 'Analyzed Sample' and can be linked.
    Store all the data in one JSON (for now)
    """
    df = pd.read_csv(file, sep="\t")

    ##
    ## Do all the verification
    ##

    messages.add_message(
        request,
        messages.SUCCESS,
        f"Upload of report successful",
    )

    return render(
        request,
        "main/modals/site_modal.html",
        {
            "object": get_instance_from_string(request.POST.get("object")),
            "type": "quicksand_upload",
        },
    )
