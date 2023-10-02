from main.models import models
from main.models import Reference, Sample, Synonym, Site, Layer, Project
from django.http import JsonResponse
from django.urls import path
from django.shortcuts import render
from main.tools.generic import get_instance_from_string
import main.tools as tools
from django.db.models import Q
import pandas as pd
import json


def sample_upload(request):
    df = pd.read_csv(request.FILES["file"], sep=",")
    df.drop_duplicates(inplace=True)

    site = get_instance_from_string(request.POST.get("instance_x"))
    all_layers = [x.name for x in site.layer.all()]

    # filter for expected/unexpected columns
    expected = Sample.table_columns()
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
        "main/samples/sample-batch-confirm.html",
        {
            "dataframe": df.fillna("").to_html(index=False, classes="table table-striped col-12"),
            "issues": issues,
            "json": df.to_json(),
            "site": site,
        },
    )


def save_verified(request):
    df = pd.read_json(request.POST.get("batch-data"))
    site = Site.objects.get(pk=int(request.POST.get("site")))
    df.convert_dtypes()

    # go through the layers
    for layer, dat in df.groupby("Layer"):
        l = Layer.objects.filter(site=site, name=layer).first()

        for sample, synonyms, type, yoc, provenience, ref in zip(
            dat["Name"],
            dat["Synonyms"],
            dat["Type"],
            dat["Year of Collection"],
            dat["Provenience"],
            dat["Reference"],
        ):
            # check if a sample exists already, get it
            s, created = Sample.objects.get_or_create(name=sample, layer=l)
            # add project
            project = Project.objects.get(namespace=request.session["session_project"])
            s.project.add(project)
            # add synonyms
            # since synonyms are stored as id_label:id, id_label2:id2
            if synonyms == synonyms:
                sample_synonyms = s.synonyms.all()
                for syn in synonyms.split(","):
                    syn_label, syn_name = syn.split(":", 1)
                    syn_label = syn_label.strip()
                    syn_name = syn_name.strip()
                    try:
                        # update
                        sample_syn = sample_synonyms.get(type=syn_label)
                        sample_syn.name = syn_name
                        sample_syn.save()
                    except:
                        # save
                        sample_syn = Synonym(name=syn_name, type=syn_label)
                        sample_syn.save()
                        sample_syn.refresh_from_db()
                        s.synonyms.add(sample_syn)
            # Type
            s.type = type
            # year of collection
            s.year_of_collection = int(yoc) if yoc == yoc else None
            # provenience
            # thats a json, so collect key:value pairs from the cell...
            try:
                prov = json.loads(s.provenience)
            except TypeError:
                # doesnt exist yet
                prov = json.loads("{}")
            new_prov = dict()
            if provenience and provenience == provenience:
                for item in provenience.split(","):
                    k, v = item.split(":")
                    new_prov[k.strip()] = v.strip()
            prov.update(new_prov)
            s.provenience = json.dumps(prov)
            s.save()

    return JsonResponse({"status": True})


urlpatterns = [
    path("upload", sample_upload, name="main_sample_upload"),
    path("save", save_verified, name="ajax_save_verified_samples"),
]
