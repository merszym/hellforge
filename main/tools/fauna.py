from main.models import models
from main.models import Reference, FaunalResults, LayerAnalysis, Layer
from django.http import JsonResponse
from django.urls import path
from django.shortcuts import render
from main.tools.generic import get_instance_from_string
import main.tools as tools
from django.db.models import Q
import pandas as pd
import json


def handle_faunal_table(request, file):

    def return_error(request, issues, df):
        return render(
            request,
            "main/modals/layer_modal.html",
            {
                "object": get_instance_from_string(request.POST.get("object")),
                "type": "faunal_errors",
                "dataframe": df.fillna("").to_html(
                    index=False, classes="table table-striped col-12"
                ),
                "issues": issues,
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
        ["Site Name", "Layer Name", "Reference", "Method"]
    ].drop_duplicates()  # get the LayerAnalysis fields
    analyses["pk"] = ""

    ## 2. create LayerAnalysis entries

    layer_analyses = []

    for i, data in analyses.iterrows():
        layer = Layer.objects.get(
            site__name=data["Site Name"].strip(), name=data["Layer Name"].strip()
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
        ana, created = LayerAnalysis.objects.get_or_create(
            layer=layer, ref=reference, type="Fauna"
        )
        layer_analyses.append(ana)
        # clear the related faunal results
        ana.faunal_results.clear()
        # TODO: delete the now orphan faunal_results
        # update or set the method
        ana.method = data["Method"]
        ana.save()
        # now add the pk to the analyses df, as we need this to then attach the faunal
        # analysis
        analyses.loc[i, "pk"] = ana.pk

    ## 3. Merge the pk of the Analysis entry back into the original df

    df = df.merge(
        analyses,
        on=["Site Name", "Layer Name", "Reference", "Method"],
        validate="m:1",
        how="left",
    )

    ## 4. Create a FaunalResults object per line, attach to the LayerAnalysis object
    ### Find the additional columns
    res = [x for x in df.columns if x not in expected_columns and x != "pk"]
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
        tmp.results = json.dumps({x: data[x] for x in res})
        tmp.save()
        faunal_results.append(tmp)

    return render(
        request,
        "main/modals/layer_modal.html",
        {
            "object": get_instance_from_string(request.POST.get("object")),
            "type": "faunal_success",
            "faunal_results": faunal_results,
            "layer_analyses": layer_analyses,
        },
    )
