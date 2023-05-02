from main.models import models
from django.http import JsonResponse
from django.urls import path
from django.shortcuts import render


def fauna_upload(request):
    # handle the csv upload --> #TODO: make a verification!
    # render into new modal, so that people can verify
    # dont save anything yet, but process how it will be saved! show the table
    # TODO: maybe make a general upload-helper function, independant of the model!
    # TODO: verify required columns

    import pandas as pd

    df = pd.read_csv(request.FILES["file"], sep=",")
    df.drop_duplicates(inplace=True)

    site = get_instance_from_string(request.POST.get("instance_x")).site
    all_layers = [x.name for x in site.layer.all()]

    # filter for expected/unexpected columns
    expected = ["Layer", "Species", "Reference"]
    issues = []
    if dropped := [x for x in df.columns if x not in expected]:
        issues.append(f"Dropped Table Columns: {','.join(dropped)}")
    df = df[[x for x in df.columns if x in expected]]

    # hardcode the testing for now
    if "Reference" in df.columns:
        df["Reference"] = df.Reference.apply(lambda x: tools.references.find(x))
        if "Not Found" in set(df["Reference"]):
            issues.append("Reference was not found (see Table)")

    layer_wrong = df[df.Layer.isin(all_layers) == False].copy()
    if len(layer_wrong) > 0:
        issues.append(f"Removed non-existing Layers: {','.join(set(layer_wrong['Layer']))}")
        df.drop(layer_wrong.index, inplace=True)
    return render(
        request,
        "main/dating/dating-batch-confirm.html",
        {
            "dataframe": df.fillna("").to_html(index=False, classes="table table-striped col-12"),
            "issues": issues,
            "json": df.to_json(),
            "site": site,
        },
    )


urlpatterns = [
    path("upload", fauna_upload, name="fauna_upload"),
]
