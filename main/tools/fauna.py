from main.models import models
from main.models import Reference, FaunalResults, LayerAnalysis, Layer, Culture, Site
from django.http import JsonResponse
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
            val = (
                int(variables[variable])
                if variables[variable] == variables[variable]
                else None
            )
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
            data["data"][entry.analysis][spec_key][var] = (
                int(val) if val == val else None
            )
            try:
                data["data_collapsed"][entry.analysis][entry.family][var] += val
            except:
                data["data_collapsed"][entry.analysis][entry.family][var] = val

    return data


def get_fauna_tab(
    request, pk, type="all", reference="all", collapse=True, by_layer=True
):

    site = Site.objects.get(pk=pk)
    project = tools.projects.get_project(request)

    # check the POST parameters
    if request.method == "POST":
        reference = request.POST.get("reference")
        type = request.POST.get("type")
        collapse = "on" == request.POST.get("collapse", "")

    ## Create the table here that is then parsed in the html view
    # 1. Get all the analyses (layer+reference)
    try:
        analyses = sorted(list(set(LayerAnalysis.objects.filter(
            Q(layer__site=site) | Q(site=site) & Q(type="Fauna")
        ))), key=lambda x: (
                getattr(x.ref, 'short', 'ZZ'), 
                getattr(x.layer.profile_junction.first(),"position","") if x.layer else 0, 
                getattr(x,'culture',''),
                getattr(x,'site','')
            )
        )
    except AttributeError: # no layer
        pass

    # hide entries without reference if not authenticated or not in project
    if not request.user.is_authenticated:
        try:
            if not site in project.site.all():
                analyses = [x for x in analyses if x.ref]
        except AttributeError:  # no project selected
            analyses = [x for x in analyses if x.ref]

    # check the reference filter
    if reference != "all":
        reference = get_instance_from_string(reference)
        analyses = [x for x in analyses if x.ref == reference]

    # now get the faunal results from the remaining analysis objects
    entries = FaunalResults.objects.filter(Q(analysis__in=analyses))

    # check the filters for small or big mammals
    if type == "small mammals":
        orders = get_small_mammals()
        entries = entries.filter(order__in=orders)
        analyses = [x for x in analyses if x.faunal_results.first() in entries]
        #analyses = analyses.filter(faunal_results__in=entries).distinct()
    if type == "large mammals":
        orders = get_small_mammals()
        entries = entries.exclude(order__in=orders)
        analyses = [x for x in analyses if x.faunal_results.first() in set(entries)]
        #analyses = analyses.filter(faunal_results__in=entries).distinct()

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

    # define the order of families based on the highest assignment
    sorting = sorted(list(data["sorting"]), key=lambda x: -1 * data["sorting"][x])
    families = sorted(
        entries.values_list("family", flat=True).distinct(),
        key=lambda x: sorting.index(x),
    )

    # make sure to preserve family namespace
    species = sorted(
        entries.values_list("family", "scientific_name").distinct(),
        key=lambda x: sorting.index(x[0]),
    )
    # and check if no "empty" headers might cause a shift
    species = [
        f"{family}__{species}"
        for family, species in species
        if len(data["header"][f"{family}__{species}"]) > 0
    ]

    # this is for the filters in the view
    all_refs = Reference.objects.filter(
        Q(layer_analysis__layer__site=site)
        | Q(layer_analysis__site=site) & Q(layer_analysis__type="Fauna")
    ).distinct()

    return render(
        request,
        "main/site/site-fauna-content.html",
        {
            "object": site,
            "data": data,
            "families": families,
            "species": species,
            "analyses": analyses,
            "all_refs": all_refs,
            "reference": reference,
            "type": type,
            "by_layer": by_layer,
            "collapse": collapse,
        },
    )


def handle_faunal_table(request, file):

    site = get_instance_from_string(request.POST.get("object"))

    def return_error(request, issues, df):

        messages.add_message(request, messages.WARNING, issues)

        return render(
            request,
            "main/modals/site_modal.html",
            {
                "object": get_instance_from_string(request.POST.get("object")),
                "type": "faunal_errors",
                "dataframe": df.fillna("").to_html(
                    index=False, classes="table table-striped col-12"
                ),
            },
        )

    df = pd.read_csv(file, sep=",")
    df.drop_duplicates(inplace=True)
    # All required information is in the table

    ## 0. Verify the data-table
    expected_columns = FaunalResults.table_columns()
    ## there can be more, but check that all required are in

    if not all(x in df.columns for x in expected_columns):
        missing = [x for x in expected_columns if x not in df.columns]
        issues = [f"Missing Table Columns: {x}" for x in missing]

        return return_error(request, issues, df)

    ## 1. Get the unique information to create LayerAnalysis entries

    analyses = df[
        ["Site Name", "Layer Name", "Culture Name", "Reference", "Method"]
    ].drop_duplicates()  # get the LayerAnalysis fields
    analyses["pk"] = ""

    ## 2. create LayerAnalysis entries
    layer_analyses = []

    for i, data in analyses.iterrows():
        # sometimes a faunal analaysis is linked to the site directly...
        layer = False
        culture = False

        if data["Layer Name"] == data["Layer Name"]:
            try:
                layer = Layer.objects.get(site=site, name=data["Layer Name"].strip())
            except Layer.DoesNotExist:
                return return_error(
                    request,
                    [f'Layer: {data["Layer Name"]} doesnt exist'],
                    pd.DataFrame(
                        {k: v for k, v in zip(data.index, data.values)}, index=[0]
                    ),
                )
        # sometimes its linked to the culture of a site
        if data["Culture Name"] == data["Culture Name"]:
            try:
                culture = Culture.objects.get(name=data["Culture Name"].strip())
            except Culture.DoesNotExist:
                return return_error(
                    request,
                    [f'Culture: {data["Culture Name"]} doesnt exist in the database'],
                    pd.DataFrame(
                        {k: v for k, v in zip(data.index, data.values)}, index=[0]
                    ),
                )

        reference = tools.references.find(data["Reference"])
        if reference == "Not Found":
            issues = [f"Reference not in found: {data['Reference']}"]
            return return_error(
                request,
                issues,
                pd.DataFrame(
                    {k: v for k, v in zip(data.index, data.values)}, index=[0]
                ),
            )
        # get or create the LayerAnalysis object
        if layer:
            ana, created = LayerAnalysis.objects.get_or_create(
                layer=layer, ref=reference, type="Fauna"
            )
        elif culture:
            ana, created = LayerAnalysis.objects.get_or_create(
                site=site, culture=culture, ref=reference, type="Fauna"
            )
        else:
            ana, created = LayerAnalysis.objects.get_or_create(
                site=site, ref=reference, type="Fauna"
            )
        layer_analyses.append(ana)
        # clear the related faunal results
        ana.faunal_results.clear()
        ana.method = data["Method"]
        ana.save()
        # now add the pk to the analyses df, as we need this to then attach the faunal
        # analysis
        analyses.loc[i, "pk"] = ana.pk

    ## 3. Merge the pk of the Analysis entry back into the original df

    df = df.merge(
        analyses,
        on=["Site Name", "Layer Name", "Culture Name", "Reference", "Method"],
        validate="m:1",
        how="left",
    )

    ## 4. Create a FaunalResults object per line, attach to the LayerAnalysis object
    ### Find the additional columns
    res = [
        x
        for x in df.columns
        if x not in expected_columns and bool(re.search("^(pk|Unnamed)", x)) == False
    ]
    faunal_results = []

    for i, data in df.iterrows():
        # first get all the required information
        tmp, created = FaunalResults.objects.get_or_create(
            order=data["Order"],
            family=data["Family"],
            scientific_name=data["Scientific Name"],
            taxid=data["TaxID"],
            analysis=LayerAnalysis.objects.get(pk=data["pk"]),
        )
        # now take the additional table-columns and create/update the results as json
        # make sure not to include 'nan' values
        tmp.results = json.dumps({x: data[x] for x in res if data[x] == data[x]})
        tmp.save()
        faunal_results.append(tmp)

    return render(
        request,
        "main/modals/site_modal.html",
        {
            "object": get_instance_from_string(request.POST.get("object")),
            "type": "faunal_success",
            "faunal_results": faunal_results,
            "layer_analyses": layer_analyses,
        },
    )


def download_faunal_table(request):
    def to_table(entry):
        columns = FaunalResults.table_columns()
        data = entry.data
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
        Q(analysis__layer__site=site)
        | Q(analysis__site=site) & Q(analysis__type="Fauna")
    ).order_by("analysis__layer")

    
    data = []
    for entry in entries:
        tmp = json.loads(to_table(entry).to_json(orient="records"))
        data.extend(tmp)
    
    columns = {}
    [columns.update(x) for x in data]
    
    return download_csv(data, columns=columns.keys(), name=f"{site.name.replace(' ','_')}_faunal_overview.csv")


urlpatterns = [
    path("<int:pk>/get-tab", get_fauna_tab, name="main_site_fauna_get"),
    path("download", download_faunal_table, name="download_faunal_table"),
]
