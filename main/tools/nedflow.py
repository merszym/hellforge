## this file is related to functions handling quicksand report-files
import pandas as pd
import seaborn as sns
from django.contrib import messages
from django.shortcuts import render
from django.urls import path
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q
from main.tools.generic import get_instance_from_string
from main.tools.projects import get_project
from main.tools.analyzed_samples import update_query_for_negatives, get_libraries, LIBRARY_LAYER_RELATED, probe_translations, paginate_rows, sort_libraries
from main.tools.dna_filters import get_analysis_settings
from main.models import NedflowAnalysis, AnalyzedSample, Site, Taxonomy
import re
import json
from collections import defaultdict

# the Taxonomy only links family -> order, these are the mammalian orders to group the legend
MAMMALIAN_ORDERS = [
    "Afrosoricida", "Artiodactyla", "Carnivora", "Cetacea", "Cetartiodactyla", "Chiroptera",
    "Cingulata", "Dasyuromorphia", "Dermoptera", "Didelphimorphia", "Diprotodontia", "Erinaceomorpha",
    "Eulipotyphla", "Hyracoidea", "Lagomorpha", "Macroscelidea", "Microbiotheria", "Monotremata",
    "Notoryctemorphia", "Paucituberculata", "Peramelemorphia", "Perissodactyla", "Pholidota", "Pilosa",
    "Primates", "Proboscidea", "Rodentia", "Scandentia", "Sirenia", "Soricomorpha", "Tubulidentata",
]
UNKNOWN_ORDER = "Unknown order"


def get_family_orders():
    """
    the {family: order} dict of the Taxonomy (stored as json-string)
    """
    taxonomy = Taxonomy.objects.filter(type="family_order").first()
    if not taxonomy or not taxonomy.data:
        return {}
    return json.loads(taxonomy.data) if isinstance(taxonomy.data, str) else taxonomy.data


def group_families(colors):
    """
    group the (family, color) legend-entries into mammals, other vertebrates and families without an order
    """
    orders = get_family_orders()
    groups = {"Mammals": [], "Other vertebrates": [], UNKNOWN_ORDER: []}
    for family, color in colors:
        order = orders.get(family)
        if not order or order == "Unassigned":
            groups[UNKNOWN_ORDER].append((family, color))
        elif order in MAMMALIAN_ORDERS:
            groups["Mammals"].append((family, color))
        else:
            groups["Other vertebrates"].append((family, color))
    return [(group, entries) for group, entries in groups.items() if entries], sorted(set(orders.values()))


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
    fampercent=1,
    families_selected=None
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
    # selected families without (filtered) results stay in the legend (grey), so they can be deselected
    colors += [(family, "#bbbbbb") for family in families_selected or [] if family not in families]
    legend_groups, known_orders = group_families(colors)

    if positives:
        query = query.filter(analyzedsample__in=positive_samples)

    # only the libraries with (filtered) results in any of the selected families
    families_selected = families_selected or []
    if families_selected:
        query = [
            entry for entry in query
            if any(family in results.get(entry, {}) for family in families_selected)
        ]

    return {
        "quicksand_results": results,
        "object_list": query,
        "colors": colors,
        "ancient": ancient,
        "positives": positives,
        "only_project": only_project,
        "fampercent": fampercent,
        "families_selected": families_selected,
        "legend_groups": legend_groups,
        "unknown_families": dict(legend_groups).get(UNKNOWN_ORDER, []),
        "known_orders": known_orders,
    }


def table_rows(request, site):
    """
    the (filtered) rows of the nedflow table, for the table and the download of the selection
    """
    # first, get the objects
    analyzed_samples = get_libraries(request, site.pk, return_query=True)

    #order by analyzed sample to match the order of the table above the quicksand tab
    query = NedflowAnalysis.objects.filter(analyzedsample__in=analyzed_samples).select_related(
        *[f'analyzedsample__{x}' for x in LIBRARY_LAYER_RELATED]
    )
    # the same order as the library-table
    query = sort_libraries(request, query, site, prefix="analyzedsample__")


    # the settings are set in the side-panel of the DNA tab (main/tools/dna_filters.py)
    settings = get_analysis_settings(request, "nedflow")
    return prepare_data(
        request,
        query,
        ancient=settings["ancient"],
        positives=settings["positives"],
        only_project=settings["only_project"],
        fampercent=settings["fampercent"],
        families_selected=settings["family"],
    )


def get_nedflow_tab(request, pk):
    """
    In the DNA Tab, render the NED-Flow table
    """
    site = Site.objects.get(pk=int(pk))
    context = {"object": site, "probe_names": probe_translations()}

    context.update(table_rows(request, site))

    # only the rows of the table are paginated, the colors etc. are calculated from all rows
    context.update(paginate_rows(request, context["object_list"]))

    return render(request, "main/nedflow/nedflow-content.html", context)

def get_data_for_export(data, nedversion, project=None, **kwargs):
    #project gets handled via the **kwargs arguments in the generic export
    if project:
        params = json.loads(project.parameters) if project.parameters else \
            {
                'nedflow_cutoff_percentage': 1,
            }
    else:
        params = {
                'nedflow_cutoff_percentage': 1,
            }

    percentage = float(params.get('nedflow_cutoff_percentage', 1))

    export = {
        "NED_version": nedversion,
        "NED_SeqsInAncientTaxa": 0,
        "NED_Ancient": "-",
        "NED_AncientTaxa": [],
        "NED_OtherTaxa": [],
        "NED_Subsitutions": [],
    }

    data = json.loads(data)

    if len(data) == 0:
        return export

    total_counts = sum(
        data[fam][0]['sum_genus_family'] for fam in data
    )

    for family in data:
        entry = data[family][0]

        try:
            fam_percentage = float(entry["sum_genus_family"] / total_counts) * 100
        except ZeroDivisionError:
            continue
        
        if fam_percentage < percentage:
            continue

        if entry["ancientness"] == "+":
            # update the export only if not already marked as ancient
            if export["NED_Ancient"] == "-":
                export["NED_Ancient"] = "+"
        if entry["ancientness"] == "++":
            export["NED_SeqsInAncientTaxa"] = export["NED_SeqsInAncientTaxa"] + entry["sum_genus_family"]
            export["NED_Ancient"] = "++"

            export["NED_AncientTaxa"].append(
                f"{family}({entry['sum_genus_family']}[{fam_percentage:.2f}%])"
            )
        else:
            export["NED_OtherTaxa"].append(
                f"{family}({entry['sum_genus_family']}[{fam_percentage:.2f}%])"
            )

        # reformat the subsitutions
        deam5 = (
            f"{entry['deam5p_pct']}[{entry['deam5p_CI_pct']}]"
        )
        deam3 = (
            f"{entry['deam3p_pct']}[{entry['deam3p_CI_pct']}]"
        )
        export["NED_Subsitutions"].append(f"{family}({deam5},{deam3})")

    # now remove the lists
    export["NED_AncientTaxa"] = (
        " ".join(export["NED_AncientTaxa"]) if len(export["NED_AncientTaxa"]) > 0 else "-"
    )
    export["NED_OtherTaxa"] = (
        " ".join(export["NED_OtherTaxa"]) if len(export["NED_OtherTaxa"]) > 0 else "-"
    )
    export["NED_Subsitutions"] = (
        " ".join(export["NED_Subsitutions"]) if len(export["NED_Subsitutions"]) > 0 else "-"
    )

    return export


@login_required
@require_POST
def set_family_order(request):
    """
    set the order of a family in the Taxonomy (from the legend of the NED-Flow tab)
    """
    family = request.POST.get("family", "").strip()
    order = request.POST.get("order", "").strip()
    if not family or not order:
        return HttpResponseBadRequest("family and order are required")

    # the same entry as in get_family_orders
    taxonomy = Taxonomy.objects.filter(type="family_order").first() or Taxonomy(type="family_order")
    data = get_family_orders()
    data[family] = order
    taxonomy.data = json.dumps(data)
    taxonomy.save()
    return HttpResponse(status=204)


urlpatterns = [
    path("get-table/<int:pk>", get_nedflow_tab, name="main_site_getnedflow"),
    path("family-order", set_family_order, name="main_nedflow_setfamilyorder"),
]