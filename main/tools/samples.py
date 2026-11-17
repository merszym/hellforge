from main.models import models
from main.models import Reference, Sample, Synonym, Site, Layer, Project, SampleBatch
from main.forms import SampleBatchForm
from django.http import JsonResponse
from django.urls import path
from django.shortcuts import render
from django.template.loader import render_to_string
from main.tools.generic import get_instance_from_string
import main.tools as tools
from django.db.models import Q
import pandas as pd
import json
import io
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
        # the gallery-tile of the image: added to the sample-batch gallery without reloading the page
        "html": render_to_string("main/samples/gallery-image.html", {"image": image}, request=request) if image.pk else "",
    }
    return JsonResponse(res)


def handle_samplebatch_file(request, file):
    df = pd.read_csv(file, sep=",")
    df.drop_duplicates(inplace=True)

    batch = SampleBatch.objects.get(pk=int(request.GET.get("batch", None)))
    site = batch.site

    all_layers = [x.name for x in site.layer.all()]
    all_fossils = [x.name for x in Sample.objects.filter(site=site, domain='archaeology')]

    # filter for expected/unexpected columns ('object': the sample to update, see the download for upload)
    expected = ["object"] + Sample.table_columns()
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

    fossil_wrong = df[
        (df["Fossil Remain"].isin(all_fossils) == False)
        & (df["Fossil Remain"] == df["Fossil Remain"])
    ].copy()

    # remove unknown parents
    if len(layer_wrong) > 0:
        issues.append(
            f"Removed non-existing Layers: {','.join(set(layer_wrong['Layer Name']))}"
        )
        df.drop(layer_wrong.index, inplace=True)
    
    if len(fossil_wrong) > 0:
        issues.append(
            f"Removed non-existing Fossils: {','.join(set(fossil_wrong['Fossil Remain']))}"
        )
        df.drop(fossil_wrong.index, inplace=True)

    # the samples to update ('object': sample_<pk> of this site) and the new samples (unique names at the site)
    if "object" not in df.columns:
        df.insert(0, "object", None)
    df["object"] = df["object"].apply(lambda x: str(x).strip() if x == x and str(x).strip() else None)
    df["Sample Name"] = df["Sample Name"].apply(lambda x: str(x).strip() if x == x and str(x).strip() else None)
    site_samples = {s.pk: s.name for s in Sample.objects.filter(site=site)}
    remove, names = [], {}
    for index, row in df.iterrows():
        obj, name = row["object"], row["Sample Name"]
        if not name:
            issues.append(f"Removed row without Sample Name{f' ({obj})' if obj else ''}")
            remove.append(index)
            continue
        if obj:
            model, _, pk = obj.partition("_")
            if model != "sample" or not pk.isdigit() or int(pk) not in site_samples:
                issues.append(f"Removed {name}: object '{obj}' is not a sample of this site")
                remove.append(index)
                continue
            pk = int(pk)
        else:
            pk = None
        # the name must stay unique at the site (new samples, renamed samples)
        if other := [k for k, v in site_samples.items() if v == name and k != pk]:
            hint = "" if pk else f" (to update it, add sample_{other[0]} in the 'object' column)"
            issues.append(f"Removed {name}: a sample with this name exists at the site{hint}")
            remove.append(index)
            continue
        if name in names or (pk and pk in names.values()):
            issues.append(f"Removed {name}: more than once in the sheet")
            remove.append(index)
            continue
        names[name] = pk
    df.drop(remove, inplace=True)

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


def present(value):
    """a value of the upload-sheet is given (not empty, None or NaN: empty cells come back as None from the json)"""
    return value is not None and value == value and str(value).strip() != ""


@login_required
def save_verified(request):
    df = pd.read_json(io.StringIO(request.POST.get("batch-data")))
    upload_batch = SampleBatch.objects.filter(pk=request.POST.get("batch") or None).first()
    site = Site.objects.get(pk=int(request.POST.get("site")))
    df.convert_dtypes()

    # go through the layers
    df["Layer Name"] = df["Layer Name"].fillna("unknown")
    if "object" not in df.columns:
        df["object"] = None
    for layer, dat in df.groupby("Layer Name"):
        if layer == "unknown":
            l = None
        else:
            l = Layer.objects.filter(site=site, name=layer).first()

        for (
            obj,
            batch,
            fossil,
            sample,
            synonyms,
            type,
            yoc,
            provenience,
        ) in zip(
            dat["object"],
            dat["Sample Batch"],
            dat["Fossil Remain"],
            dat["Sample Name"],
            dat["Sample Synonyms"],
            dat["Sample Type"],
            dat["Sample Year of Collection"],
            dat["Sample Provenience"],
        ):
            # 'object': update this sample (also its name), otherwise a new sample (the name must be unique at the site)
            if present(obj):
                s = Sample.objects.get(pk=int(str(obj).split("_")[1]), site=site)
                if Sample.objects.filter(site=site, name=sample).exclude(pk=s.pk).exists():
                    continue
                s.name = sample
            else:
                if Sample.objects.filter(site=site, name=sample).exists():
                    continue
                s = Sample.objects.create(name=sample, site=site)
            # if layer is given: Update the layer
            if present(fossil):
                # the sample gets the layer of the parent (see Sample.save)
                parent = Sample.objects.get(site=site, domain='archaeology', name=fossil)
                s.sample = parent
            else:
                s.layer = l

            batch = SampleBatch.objects.get(site=site, name=batch)
            s.batch = batch
            # add project
            project = Project.objects.get(namespace=request.session["session_project"])
            s.project.add(project)
            # add synonyms
            # since synonyms are stored as id_label:id, id_label2:id2
            if present(synonyms):
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
            s.year_of_collection = int(float(yoc)) if present(yoc) else None
            # provenience
            # thats a json, so collect key:value pairs from the cell...
            try:
                prov = json.loads(s.provenience)
            except TypeError:
                # doesnt exist yet
                prov = json.loads("{}")
            new_prov = dict()
            if present(provenience):
                for item in provenience.split(";"):
                    k, v = item.split(":")
                    new_prov[k.strip()] = v.strip()
            prov.update(new_prov)
            s.provenience = json.dumps(prov)
            s.save()

    from main.tools.site import get_site_samplebatch_tab

    return get_site_samplebatch_tab(request, upload_batch.pk if upload_batch else batch.pk)


def add_human_remain(request):
    # add a human remains entry from the browser
    site = get_instance_from_string(request.POST.get('site'))
    # create the samples
    Sample(
        domain='archaeology',
        name="unnamed remain",
        site = site,
    ).save()

    from main.tools.site import get_site_human_content
    
    return get_site_human_content(request, site.pk)



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
        try:
            # the sample gets the layer of the fossil (see Sample.save)
            fossil = Sample.objects.get(pk=int(request.POST.get('sample')))
            sample.sample = fossil
        except:
            sample.sample = None
        sample.save()
    return render(
        request,
        "main/modals/sample_modal.html",
        {"object": sample, "type": "edit_layer"},
    )


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

        sample.name = request.POST.get("name")
        sample.type = request.POST.get("type", None)
        if request.POST.get("year_of_collection") == "":
            sample.year_of_collection = None
        else:
            sample.year_of_collection = request.POST.get("year_of_collection")
        sample.hominin_group = request.POST.get("hominin_group", None)
        sample.note = request.POST.get("note", None)

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
    path("add", add_human_remain, name="main_sample_create"),
    path("update-base", update_samplebase, name="sample-edit"),
    path("update-layer", update_samplelayer, name="sample-layer-update"),
    path("update-batch", update_samplebatch, name="sample-batch-update"),
    path("edit-provenience", update_sample_provenience, name="sample-provenience-edit"),
]
