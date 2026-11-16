
from main.models import AnalyzedSample, HumanDiagnosticPositions, Site
from main.tools.generic import get_instance_from_string
from main.tools.projects import get_project
from main.tools.analyzed_samples import get_libraries, LIBRARY_LAYER_RELATED, probe_translations, paginate_rows, sort_libraries
from main.tools.dna_filters import get_analysis_settings

import pandas as pd
import seaborn as sns
import json

from django.shortcuts import render
from django.contrib import messages
from django.urls import path
from main.tools.analyzed_samples import update_query_for_negatives
from django.db.models import Q
from collections import defaultdict
import re
from scipy.stats import beta


# diagnostic positions that are excluded from the lineage tests (in the table, the downloads and the image-overlay):
# their supporting fragments are removed and the significance is recalculated (as in the summary script)
BLACKLISTED_POSITIONS = {2955}
HOMININ_LINEAGES = ["H", "N", "N-HST", "HST", "D", "D-S", "S"]
# e.g. '^^^54.4% (255 / 469)': significance (^, ^^, ^^^), the supporting (diagnostic) fragments / all
SUPPORT = re.compile(r"^(\^*)\S*% \((\d+) / (\d+)\)")
# the supporting fragments per diagnostic position, e.g. '(2056:8)(2523:9)' (their sum: the supporting fragments above)
DERIVED = re.compile(r"\((\d+):(\d+)\)")


def significance_marker(fragments, total, positions, min_positions=3):
    """
    the lineage test of the summary script (sediment_summary_quicksand_v2.1.pl, -human), with the lower bound of the
    95% confidence interval (Clopper-Pearson) of the support (fragments / total):
    '^' significantly more than 5% support, '^^' more than 10%, '^^^' more than 10% and at least 3 different positions.
    reproduces all markers stored in the database
    """
    if total <= 0:
        return ""
    lower = beta.ppf(0.025, fragments, total - fragments + 1) * 100 if fragments else 0
    if lower >= 10:
        return "^^^" if positions >= min_positions else "^^"
    if lower >= 5:
        return "^"
    return ""


def apply_blacklist(data):
    """
    the report (dict) without the blacklisted diagnostic positions: for each lineage (all and deaminated sequences)
    the supporting fragments at these positions are removed from X_der and X_support, the support and its significance
    are recalculated. the ancestral fragments per position are not reported: only the supporting fragments are removed
    from the total. lineages without a blacklisted position are not changed
    """
    data = dict(data)
    for lineage in HOMININ_LINEAGES:
        for support_key, derived_key in [(f"{lineage}_support", f"{lineage}_der"), (f"{lineage}_support_deam", f"{lineage}_deam_der")]:
            positions = [(int(position), int(count)) for position, count in DERIVED.findall(str(data.get(derived_key) or ""))]
            removed = sum(count for position, count in positions if position in BLACKLISTED_POSITIONS)
            match = SUPPORT.match(str(data.get(support_key) or ""))
            if not removed or not match:
                continue
            kept = [(position, count) for position, count in positions if position not in BLACKLISTED_POSITIONS]
            fragments, total = int(match.group(2)) - removed, int(match.group(3)) - removed
            percent = f"{fragments / total * 100:.1f}" if total else "NA"
            marker = significance_marker(fragments, total, sum(1 for _, count in kept if count))
            data[support_key] = f"{marker}{percent}% ({fragments} / {total})"
            data[derived_key] = "".join(f"({position}:{count})" for position, count in kept) or None
    return data



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
    extended=False,
    only_project=True
):

    lineages = []  # for the colors
    nested_dict = lambda: defaultdict(nested_dict)
    positive_samples = []
    results = nested_dict()
    project = get_project(request)

    query = query.filter(analyzedsample__qc_pass=True)

    if only_project:
        query = query.filter(analyzedsample__project=project)

    for entry in query:
        data = apply_blacklist(json.loads(entry.data))
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
        "only_project": only_project,
    }


def table_rows(request, site):
    """
    the (filtered) rows of the matthias table, for the table and the download of the selection
    """
    # first, get the objects
    analyzed_samples = get_libraries(request, site.pk, return_query=True)

    query = HumanDiagnosticPositions.objects.filter(analyzedsample__in=analyzed_samples).select_related(
        *[f'analyzedsample__{x}' for x in LIBRARY_LAYER_RELATED]
    ).prefetch_related("analyzedsample__sample__image_annotations")  # the images the sample is tagged on (eye-icon)
    # the same order as the library-table
    query = sort_libraries(request, query, site, prefix="analyzedsample__", default="layer")

    # the settings are set in the side-panel of the DNA tab (main/tools/dna_filters.py)
    settings = get_analysis_settings(request, "matthias")
    return prepare_data(
        request,
        query,
        ancient=settings["ancient"],
        positives=settings["positives"],
        extended=settings["extended"],
        only_project=settings["only_project"],
    )


def get_matthias_tab(request, pk):
    site = Site.objects.get(pk=int(pk))
    context = {"object": site, "probe_names": probe_translations(), "blacklisted_positions": sorted(BLACKLISTED_POSITIONS)}

    context.update(table_rows(request, site))

    # only the rows of the table are paginated, the colors etc. are calculated from all rows
    context.update(paginate_rows(request, context["object_list"]))

    return render(request, "main/matthias/matthias-content.html", context)


urlpatterns = [
    path("get-table/<int:pk>", get_matthias_tab, name="main_site_getmatthias")
]