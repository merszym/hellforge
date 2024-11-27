from main.models import models
from main.models import Reference, Sample, Synonym, Site, Layer, Project, SampleBatch
from main.forms import SampleBatchForm
from django.http import JsonResponse
from django.urls import path
from django.shortcuts import render
from main.tools.generic import get_instance_from_string
import main.tools as tools
from django.db.models import Q
import pandas as pd
import json
from django.contrib.auth.decorators import (
    login_required,
)  # this is for now, make smarter later
from main.tools.site import get_site_samplebatch_tab

# functions related to the site-view and the samplebatches

#
# #TODO: This function here doesnt make really sense... it should go into a gallery.py or something...
#


def handle_galleryimage_upload(request, file):
    """
    This is to add images to a gallery and return the expected JSON that editorJS needs to
    display a freshly uploaded file.
    """
    from main.models import Image

    # 1. get the gallery, it should exist at this point!
    gallery = get_instance_from_string(f"gallery_{request.GET.get('gallery')}")

    # 2. create a new image
    image = Image(image=file, gallery=gallery)
    image.save()
    image.refresh_from_db()

    if image.pk:
        success = 1
        url = image.image.url
    else:
        success = 0
        url = ""

    res = {
        "success": success,
        "file": {
            "url": url,
        },
    }
    return JsonResponse(res)


def handle_samplebatch_file(request, file):
    df = pd.read_csv(file, sep=",")
    df.drop_duplicates(inplace=True)

    batch = SampleBatch.objects.get(pk=int(request.GET.get("batch", None)))
    site = batch.site

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

    layer_wrong = df[
        (df["Layer Name"].isin(all_layers) == False)
        & (df["Layer Name"] == df["Layer Name"])
    ].copy()
    if len(layer_wrong) > 0:
        issues.append(
            f"Removed non-existing Layers: {','.join(set(layer_wrong['Layer Name']))}"
        )
        df.drop(layer_wrong.index, inplace=True)

    # add the sample batch
    df.insert(0, "Sample Batch", batch.name)

    return render(
        request,
        "main/modals/site_modal.html",
        {
            "type": "samplebatch_upload_confirm",
            "dataframe": df.fillna("").to_html(
                index=False, classes="table table-striped col-12"
            ),
            "issues": issues,
            "json": df.to_json(),
            "batch": batch,
            "site": site,
        },
    )


def save_verified(request):
    df = pd.read_json(request.POST.get("batch-data"))
    site = Site.objects.get(pk=int(request.POST.get("site")))
    df.convert_dtypes()

    # go through the layers
    df["Layer Name"] = df["Layer Name"].fillna("unknown")
    for layer, dat in df.groupby("Layer Name"):
        if layer == "unknown":
            l = None
        else:
            l = Layer.objects.filter(site=site, name=layer).first()

        for (
            batch,
            sample,
            synonyms,
            type,
            yoc,
            provenience,
        ) in zip(
            dat["Sample Batch"],
            dat["Sample Name"],
            dat["Sample Synonyms"],
            dat["Sample Type"],
            dat["Sample Year of Collection"],
            dat["Sample Provenience"],
        ):
            # check if a sample exists already, get it
            s, created = Sample.objects.get_or_create(name=sample, layer=l, site=site)
            # if layer is given: Update the layer
            s.layer = l
            # get the batch
            batch = SampleBatch.objects.get(site=site, name=batch)
            s.batch = batch
            # add project
            project = Project.objects.get(namespace=request.session["session_project"])
            s.project.add(project)
            # add synonyms
            # since synonyms are stored as id_label:id, id_label2:id2
            if synonyms == synonyms and synonyms:
                sample_synonyms = s.synonyms.all()
                for syn in synonyms.split(";"):
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
                for item in provenience.split(";"):
                    k, v = item.split(":")
                    new_prov[k.strip()] = v.strip()
            prov.update(new_prov)
            s.provenience = json.dumps(prov)
            s.save()

    from main.tools.site import get_site_samplebatch_tab

    return get_site_samplebatch_tab(request, batch.pk)


# UPDATE MODALS
@login_required
def update_samplelayer(request):
    if request.method == "POST":
        sample = Sample.objects.get(pk=int(request.POST.get("object")))
        try:
            layer = Layer.objects.get(pk=int(request.POST.get("layer")))
            sample.layer = layer
        except ValueError:  # no layer pk given
            sample.layer = None
        sample.save()
    # return updated html, clear request.POST
    request.POST._mutable = True
    request.POST = {}
    return get_site_samplebatch_tab(request, sample.batch.pk)


@login_required
def update_samplebatch(request):
    if request.method == "POST":
        sample = Sample.objects.get(pk=int(request.POST.get("object")))
        old_batch = sample.batch
        try:
            batch = SampleBatch.objects.get(pk=int(request.POST.get("batch")))
            sample.batch = batch
        except ValueError:  # no layer pk given
            pass
        sample.save()
    # return updated html, clear request.POST
    request.POST._mutable = True
    request.POST = {}
    return get_site_samplebatch_tab(request, old_batch.pk)


@login_required
def update_samplebase(request):
    if request.method == "POST":
        sample = Sample.objects.get(pk=int(request.POST.get("object")))

        sample.type = request.POST.get("type", None)
        sample.year_of_collection = request.POST.get("year_of_collection", None)

        sample.save()
    # return updated html
    return render(
        request,
        "main/modals/sample_modal.html",
        {"object": sample, "type": "edit_base"},
    )


@login_required
def update_sample_provenience(request):
    sample = Sample.objects.get(pk=int(request.POST.get("object")))
    type = request.GET.get("type", False)

    try:
        provenience = json.loads(sample.provenience)
    except TypeError:
        # empty provenience array so far
        provenience = {}

    key = request.POST.get("key", False)
    val = request.POST.get("value", False)

    if type == "add" and key and val:
        provenience[key] = val

    if type == "remove" and key:
        del provenience[key]

    sample.provenience = json.dumps(provenience)
    sample.save()

    return render(
        request,
        "main/modals/sample_modal.html",
        {"object": sample, "type": "edit_provenience", "provenience": provenience},
    )


urlpatterns = [
    path("save", save_verified, name="ajax_save_verified_samples"),
    path("update-base", update_samplebase, name="sample-edit"),
    path("update-layer", update_samplelayer, name="sample-layer-update"),
    path("update-batch", update_samplebatch, name="sample-batch-update"),
    path("edit-provenience", update_sample_provenience, name="sample-provenience-edit"),
]
