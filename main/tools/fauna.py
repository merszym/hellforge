from main.models import models
from main.models import Reference, FaunalResults, LayerAnalysis, Layer, Culture, Site, ProfileLayerJunction, SpeciesTranslation
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.shortcuts import render
from main.tools.generic import get_instance_from_string, download_csv
import main.tools as tools
from django.db.models import Q
import pandas as pd
import json
from collections import defaultdict
import re
from django.contrib import messages


def get_small_mammals():
    # this is hardcoded for now :')
    orders = [
        "Rodentia",
        "Scandentia",
        "Eulipotyphla",
        "Lagomorpha",
        "Soricomorpha",
        "Chiroptera",
    ]
    return orders


def get_fauna_data(entries):
    # Lets iterate over the entries and assemble a dict

    nested_dict = lambda: defaultdict(nested_dict)
    data = nested_dict()

    for entry in entries:
        # first, get the header
        # I put the data like this:
        #
        # header:{'Familidae':[('Species', MNI),('Species', NISP)]} --> this fam requires 2 colspan
        # header:{'Species':[MNI, NISP]}
        #
        #
        # for the collapsed, I want
        # collapsed:{'Familidae':[MNI, NISP]} --> fam requires colspan 2
        #

        variables = json.loads(entry.results)

        for variable in variables.keys():
            try:
                val = (
                    int(variables[variable])
                    if variables[variable] == variables[variable]
                    else None
                )
            except:
                val = None
            # save all variables to later get the maximum (for displaying the heatmap) and for sorting
            try:
                data["max"][variable].append(val)
            except:
                data["max"][variable] = [val]

            # this is for sorting
            try:
                if val > data["sorting"][entry.family]:
                    data["sorting"][entry.family] = val
            except TypeError:
                data["sorting"][entry.family] = val

            #
            # this is for the collapsed view
            # collapsed:{ 'Familidae':[NISP, MNI] }
            #

            try:
                if variable not in data["collapsed"][entry.family]:
                    data["collapsed"][entry.family].append(variable)
            except AttributeError:
                data["collapsed"][entry.family] = [variable]

            #
            # this is for the non-collapsed table header
            #

            try:
                if (
                    not (entry.scientific_name, variable)
                    in data["header"][entry.family]
                ):
                    data["header"][entry.family].append(
                        (entry.scientific_name, variable)
                    )
            except:
                data["header"][entry.family] = [(entry.scientific_name, variable)]

            # now get the species entries
            spec_key = f"{entry.family}__{entry.scientific_name}"
            try:
                if not variable in data["header"][spec_key]:
                    data["header"][spec_key].append(variable)
            except:
                data["header"][spec_key] = [variable]

        # then, collect the data
        # with the analysis as key, we retain the layer-information
        for var, val in variables.items():
            try:
                val = int(val)
            except ValueError:
                val = None
            data["data"][entry.analysis][spec_key][var] = val
            try:
                data["data_collapsed"][entry.analysis][entry.family][var] += val
            except:
                data["data_collapsed"][entry.analysis][entry.family][var] = val

    return data


# what the sorting and the table use of an analysis, loaded in bulk
ANALYSIS_RELATED = ["layer__culture", "ref", "culture", "site"]


def get_fauna_tab(request, pk, by_layer=True):

    site = Site.objects.get(pk=pk)
    project = tools.projects.get_project(request)

    # the filter-chips (applied directly): references and large/small mammals (several or none = all),
    # 'species' shows the species instead of the families
    references = [int(x) for x in request.POST.getlist("reference") if x.isdigit()]
    types = [x for x in request.POST.getlist("type") if x in ("large", "small")]
    collapse = "species" not in request.POST

    ## Create the table here that is then parsed in the html view
    # 1. Get all the analyses (layer+reference), sorted by layer (position in the main profile), reference and method
    from main.tools.analyzed_samples import main_profile

    analyses = list(LayerAnalysis.objects.filter(
        (Q(layer__site=site) | Q(site=site)) & Q(type="Fauna")
    ).select_related(*ANALYSIS_RELATED).distinct())
    positions = dict(ProfileLayerJunction.objects.filter(profile=main_profile(site)).values_list("layer_id", "position"))

    def layer_position(layer):
        # the position of the layer, or of its closest parent layer in the profile (sub-layers are not always in it)
        return next((positions[pk] for pk in reversed(layer.path_ids) if pk in positions), None)

    def sort_key(analysis):
        layer = analysis.layer
        if layer is None:
            # analyses of the site or a culture (without layer) at the end
            return (2, 0, analysis.culture.name if analysis.culture else "", getattr(analysis.ref, "short", "~"), analysis.method or "")
        position = layer_position(layer)
        return (0 if position is not None else 1, position or 0, layer.name, getattr(analysis.ref, "short", "~"), analysis.method or "")

    analyses.sort(key=sort_key)

    # hide entries without reference if not authenticated or not in project
    if not request.user.is_authenticated:
        try:
            if not site in project.site.all():
                analyses = [x for x in analyses if x.ref]
        except AttributeError:  # no project selected
            analyses = [x for x in analyses if x.ref]

    # check the reference filter
    if references:
        analyses = [x for x in analyses if x.ref_id in references]

    # now get the faunal results from the remaining analysis objects
    entries = FaunalResults.objects.filter(Q(analysis__in=analyses)).select_related("analysis")

    # check the filters for small or large mammals (both or none: all), only the analyses with results remain
    if len(types) == 1:
        entries = entries.filter(order__in=get_small_mammals()) if types == ["small"] else entries.exclude(order__in=get_small_mammals())
        with_results = set(entries.values_list("analysis_id", flat=True))
        analyses = [x for x in analyses if x.pk in with_results]

    # 2. Get the table columns
    # Thats now a bit more complicated, as we need the headers as follows
    #
    #                      | Bovidae                      | Cervidae                | Suidae     | <-- This is the family
    #                      | Bos primigenius | Capra ibex | Dama dama  | xxxx       | Sus scrofa | <-- This is the species
    #                      | MNI | NISP      | MNI | NISP | MNI | NISP | MNI | NISP | MNI | NISP | <-- This is variable
    # Layer | Ref | Method |
    # Layer | Ref | Method |

    # Unless we collapse the family, then its
    #                      | Bovidae    | Cervidae   | Suidae      | <-- This is the family
    #                      | MNI | NISP | MNI | NISP |  MNI | NISP | <-- This is the summed variables
    # Layer | Ref | Method |
    # Layer | Ref | Method |

    # 2.1 So first we need to get the header right
    # So lets get the data from another function

    data = get_fauna_data(entries)

    # get the maximum value for each var
    for var, vals in data["max"].items():
        data["max"][var] = max([x for x in vals if x != None])

    # the structure of the table: large/small mammals -> order -> family (-> species), families by the highest assignment
    sorting = sorted(list(data["sorting"]), key=lambda x: -1 * data["sorting"][x])
    family_order = {}
    for family, order in entries.values_list("family", "order"):
        order = (order or "").strip()
        if order and order != "nan":
            family_order.setdefault(family, order)
    small = get_small_mammals()
    group_names = ["Large mammals", "Small mammals", "Unknown order"]

    def group_of(family):
        order = family_order.get(family)
        return 2 if order is None else (1 if order in small else 0)

    # within an order: counts reported on the order-level (family == order) first, then the families by abundance
    families = sorted(
        entries.values_list("family", flat=True).distinct(),
        key=lambda x: (group_of(x), family_order.get(x, ""), x != family_order.get(x), sorting.index(x)),
    )

    # make sure to preserve family namespace
    species = sorted(
        entries.values_list("family", "scientific_name").distinct(),
        key=lambda x: families.index(x[0]),
    )
    # and check if no "empty" headers might cause a shift
    species = [
        f"{family}__{species}"
        for family, species in species
        if len(data["header"][f"{family}__{species}"]) > 0
    ]

    # the columns (key: family or family__species, var) and the separators where a group, order, family or species starts
    columns = []
    previous = (None, None, None, None)
    for family in families:
        keys = [family] if collapse else [sp for sp in species if sp.split("__")[0] == family]
        for key in keys:
            for var in data["collapsed" if collapse else "header"][key]:
                current = (group_of(family), family_order.get(family), family, key)
                level = next((n for n in range(4) if current[n] != previous[n]), None)
                columns.append({"key": key, "var": var, "family": family,
                                "sep": ["group", "order", "family", "species"][level] if level is not None and columns else ""})
                previous = current

    # the header rows: consecutive columns with the same group/order/family/species are merged (colspan)
    def header_row(level, label, kind):
        # level: the columns with the same value up to this level are merged
        cells = []
        for column in columns:
            value = (group_of(column["family"]), family_order.get(column["family"]), column["family"], column["key"])[:level]
            if cells and cells[-1]["value"] == value:
                cells[-1]["colspan"] += 1
            else:
                cells.append({"value": value, "label": label(column), "colspan": 1, "sep": column["sep"], "kind": kind})
        return cells

    header_rows = [
        header_row(1, lambda c: group_names[group_of(c["family"])], "group"),
        header_row(2, lambda c: family_order.get(c["family"], ""), "order"),
        header_row(3, lambda c: c["family"], "family"),
    ]
    if not collapse:
        # the species: the translated name (SpeciesTranslation), the original name below
        translations = SpeciesTranslation.lookup()
        species_row = header_row(4, lambda c: c["key"].split("__", 1)[1], "species")
        for cell in species_row:
            family, original = cell["value"][3].split("__", 1)
            cell.update({"family": family, "original": original, "label": translations.get((family, original), original)})
        header_rows.append(species_row)

    # this is for the filters in the view
    all_refs = Reference.objects.filter(
        (Q(layer_analysis__layer__site=site) | Q(layer_analysis__site=site))
        & Q(layer_analysis__type="Fauna")
    ).distinct()

    return render(
        request,
        "main/site/site-fauna-content.html",
        {
            "object": site,
            "data": data,
            "families": families,
            "species": species,
            "columns": columns,
            "header_rows": header_rows,
            "analyses": analyses,
            "all_refs": all_refs,
            "references": references,
            "types": types,
            "by_layer": by_layer,
            "collapse": collapse,
        },
    )


def strip_whitespace(df):
    """
    remove leading/trailing whitespace from the column names and all text values of an uploaded sheet
    (e.g. ' Artiodactyla' would be a separate order)
    """
    df.columns = [str(x).strip() for x in df.columns]
    for column in df.columns:
        if df[column].dtype == object:
            df[column] = df[column].map(lambda x: x.strip() if isinstance(x, str) else x)
    return df


def faunal_value(value):
    """
    a value of the results: whole numbers stay whole numbers (pandas reads them as float, e.g. 5.0)
    """
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if hasattr(value, "item"):  # numpy types
        return faunal_value(value.item())
    return value


def handle_faunal_table(request, file):
    """
    upload of faunal results: all rows are checked first (all problems are listed), then saved all-or-nothing.
    the results of an analysis (layer/culture/site + reference) are replaced by the rows of the sheet
    """
    from django.db import transaction

    site = get_instance_from_string(request.POST.get("object"))

    def return_error(request, issues, df):
        # nothing is saved, all problems are listed
        return render(
            request,
            "main/modals/site_modal.html",
            {
                "object": site,
                "type": "faunal_errors",
                "issues": issues,
                "dataframe": df.fillna("").to_html(
                    index=False, classes="table table-striped col-12"
                ),
            },
        )

    present = lambda value: value == value and value not in ("", None)

    df = strip_whitespace(pd.read_csv(file, sep=","))
    df.drop_duplicates(inplace=True)

    ## 0. Verify the data-table
    expected_columns = FaunalResults.table_columns()
    if not all(x in df.columns for x in expected_columns):
        missing = [x for x in expected_columns if x not in df.columns]
        return return_error(request, [f"Missing Table Columns: {x}" for x in missing], df)

    ## 1. check all analyses (layer, culture, reference) before anything is saved
    analysis_columns = ["Site Name", "Layer Name", "Culture Name", "Reference", "Method"]
    # empty cells as '' (NaN is not equal to itself, the rows are used as keys)
    df[analysis_columns] = df[analysis_columns].fillna("")
    issues = []
    targets = {}  # analysis-row -> (layer, culture, reference)
    for i, data in df[analysis_columns].drop_duplicates().iterrows():
        row = tuple(data.values)
        if present(data["Site Name"]) and data["Site Name"] != site.name:
            issues.append(f"Site '{data['Site Name']}' is not this site ({site.name})")
        layer = culture = None
        if present(data["Layer Name"]):
            layers = list(Layer.objects.filter(site=site, name=data["Layer Name"])[:2])
            if not layers:
                issues.append(f"Layer '{data['Layer Name']}' doesn't exist at {site.name}")
            elif len(layers) > 1:
                issues.append(f"Layer '{data['Layer Name']}' exists more than once at {site.name}")
            else:
                layer = layers[0]
        if present(data["Culture Name"]):
            culture = Culture.objects.filter(name=data["Culture Name"]).first()
            if culture is None:
                issues.append(f"Culture '{data['Culture Name']}' doesn't exist in the database")
        reference = tools.references.find(data["Reference"])
        if reference == "Not Found":
            issues.append(f"Reference not found: {data['Reference']}")
        targets[row] = (layer, culture, reference)

    # an analysis (layer/culture + reference) can only have one method
    methods = defaultdict(set)
    for row, (layer, culture, reference) in targets.items():
        methods[(layer, culture, reference if reference != "Not Found" else None)].add(row[4] if present(row[4]) else "")
    for (layer, culture, reference), names in methods.items():
        if len(names) > 1:
            issues.append(f"{layer or culture or site} / {reference}: more than one method ({', '.join(sorted(names))})")

    # a species can only be once in an analysis
    species = df.apply(lambda d: (tuple(d[analysis_columns].values), d["Family"],
        d["Original"] if "Original" in d and present(d["Original"]) else d["Scientific Name"]), axis=1)
    if duplicated := sorted({f"{s[1]} / {s[2]} ({s[0][1] if present(s[0][1]) else s[0][2] if present(s[0][2]) else 'site'}, {s[0][3]})" for s in species[species.duplicated()]}):
        issues.append(f"Species more than once in the same analysis: {'; '.join(duplicated)}")

    if issues:
        return return_error(request, issues, df)

    ## 2. save all-or-nothing: the results of the analyses are replaced
    res = [
        x
        for x in df.columns
        if x not in expected_columns + ["Original"] and bool(re.search("^(pk|Unnamed)", x)) == False
    ]
    summary = []
    with transaction.atomic():
        analyses = {}
        for row, (layer, culture, reference) in targets.items():
            if layer:
                ana, created = LayerAnalysis.objects.get_or_create(layer=layer, ref=reference, type="Fauna")
            elif culture:
                ana, created = LayerAnalysis.objects.get_or_create(site=site, culture=culture, ref=reference, type="Fauna")
            else:
                ana, created = LayerAnalysis.objects.get_or_create(site=site, ref=reference, type="Fauna")
            ana.method = row[4] if present(row[4]) else None
            ana.save()
            analyses[row] = ana
        # remove the old results (delete, not only unlink: the results would remain without analysis)
        replaced = {}
        for ana in set(analyses.values()):
            replaced[ana.pk] = ana.faunal_results.count()
            ana.faunal_results.all().delete()

        new = defaultdict(int)
        for i, data in df.iterrows():
            ana = analyses[tuple(data[analysis_columns].values)]
            FaunalResults.objects.create(
                order=data["Order"] if present(data["Order"]) else None,
                family=data["Family"] if present(data["Family"]) else None,
                # the export has the translation in 'Scientific Name' and the uploaded name in 'Original'
                scientific_name=data["Original"] if "Original" in data and present(data["Original"]) else data["Scientific Name"],
                taxid=str(faunal_value(data["TaxID"])) if present(data["TaxID"]) else None,
                analysis=ana,
                # the additional table-columns are the results (without empty values)
                results=json.dumps({x: faunal_value(data[x]) for x in res if present(data[x])}),
            )
            new[ana.pk] += 1
        for ana in set(analyses.values()):
            summary.append({"analysis": ana, "replaced": replaced[ana.pk], "new": new[ana.pk]})

    return render(
        request,
        "main/modals/site_modal.html",
        {
            "object": site,
            "type": "faunal_success",
            "summary": sorted(summary, key=lambda x: str(x["analysis"])),
        },
    )


def download_faunal_table(request):
    translations = SpeciesTranslation.lookup()

    def to_table(entry):
        # 'Scientific Name' is the translation (SpeciesTranslation), 'Original' the uploaded name
        columns = FaunalResults.table_columns()
        data = entry.data
        position = columns.index("Scientific Name")
        data[position] = translations.get((entry.family, entry.scientific_name), entry.scientific_name)
        columns.insert(position + 1, "Original")
        data.insert(position + 1, entry.scientific_name)
        tmp = pd.DataFrame.from_dict({0: data}, columns=columns, orient="index")
        for var, val in json.loads(entry.results).items():
            tmp[var] = val
        # remove nans
        for col in tmp.columns:
            tmp[col] = tmp[col].apply(lambda x: None if x == "nan" else x)
        return tmp

    obj = request.GET.get("object")
    try:
        site = get_instance_from_string(obj)
    except:
        site = Site.objects.get(name=obj)

    entries = FaunalResults.objects.filter(
        (Q(analysis__layer__site=site) | Q(analysis__site=site)) & Q(analysis__type="Fauna")
    ).order_by("analysis__layer")

    
    data = []
    for entry in entries:
        tmp = json.loads(to_table(entry).to_json(orient="records"))
        data.extend(tmp)
    
    columns = {}
    [columns.update(x) for x in data]
    
    return download_csv(data, columns=columns.keys(), name=f"{site.name.replace(' ','_')}_faunal_overview.csv")


@login_required
def species_translation(request):
    """
    the name of a species (click on the species in the fauna-table): GET shows the modal.
    POST action=translate: the translation (SpeciesTranslation, empty name: delete), for all sites
    POST action=rename: correct the uploaded name of the results (wrong imports), at this site or at all sites
    after saving, the fauna-tab reloads (with its filters)
    """
    get = lambda key, default="": request.POST.get(key, request.GET.get(key, default)).strip()
    family, original = get("family"), get("original")
    site = Site.objects.filter(pk=get("site")).first() if get("site").isdigit() else None
    saved = renamed = False
    errors = []

    def results_of(name, all_sites=True):
        results = FaunalResults.objects.filter(family=family, scientific_name=name)
        if not all_sites and site:
            results = results.filter(Q(analysis__layer__site=site) | Q(analysis__site=site))
        return results

    if request.method == "POST" and get("action") == "rename":
        new_name = get("new_original")
        results = results_of(original, all_sites=get("scope") == "all")
        # the same species can only be once in an analysis
        if conflicts := FaunalResults.objects.filter(family=family, scientific_name=new_name, analysis__in=results.values("analysis")).select_related("analysis__layer", "analysis__ref"):
            errors.append(f"'{new_name}' is already in the analyses: {', '.join(str(x.analysis) for x in conflicts)}")
        elif new_name and new_name != original:
            results.update(scientific_name=new_name)
            original, renamed, saved = new_name, True, True
    elif request.method == "POST":
        translation = SpeciesTranslation.objects.filter(family=family, original_name=original).first()
        name = get("name")
        if not name or name == original:
            if translation:
                translation.delete()
        elif translation:
            translation.name = name
            translation.save()
        else:
            SpeciesTranslation.objects.create(family=family, original_name=original, name=name)
        saved = True

    response = render(request, "main/modals/species_translation_modal.html", {
        "family": family, "original": original, "site": site, "saved": saved, "renamed": renamed, "errors": errors,
        "translation": SpeciesTranslation.objects.filter(family=family, original_name=original).first(),
        "results": results_of(original).count(),
        "site_results": results_of(original, all_sites=False).count() if site else None,
    })
    if saved:
        response["HX-Trigger"] = "fauna-translation-changed"
    return response


urlpatterns = [
    path("<int:pk>/get-tab", get_fauna_tab, name="main_site_fauna_get"),
    path("download", download_faunal_table, name="download_faunal_table"),
    path("species-translation", species_translation, name="main_fauna_species_translation"),
]
