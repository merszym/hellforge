from main.models import models
from main.models import FaunalAssemblage, FoundTaxon, Taxon, Reference
from django.http import JsonResponse
from django.urls import path
from django.shortcuts import render
from main.tools.generic import get_instance_from_string
import main.tools as tools
from django.db.models import Q


def fauna_upload(request):
    import pandas as pd

    # TODO: create taxa upon assemblageUpload

    df = pd.read_csv(request.FILES["file"], sep=",")
    df.drop_duplicates(inplace=True)

    site = get_instance_from_string(request.POST.get("instance_x"))
    all_layers = [x.name for x in site.layer.all()]

    # filter for expected/unexpected columns
    expected = FaunalAssemblage.table_columns()
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
        "main/fauna/fauna-batch-confirm.html",
        {
            "dataframe": df.fillna("").to_html(index=False, classes="table table-striped col-12"),
            "issues": issues,
            "json": df.to_json(),
            "site": site,
        },
    )


def save_verified(request):
    import pandas as pd
    from main.models import Date, Site, Layer, Reference

    df = pd.read_json(request.POST.get("batch-data"))
    site = Site.objects.get(pk=int(request.POST.get("site")))
    df.convert_dtypes()

    # create an assemblage for each layer!
    for layer, dat in df.groupby(["Layer"]):
        tmp_layer = Layer.objects.filter(Q(site=site) & Q(name=layer)).first()

        assemblage = FaunalAssemblage.objects.filter(layer=tmp_layer).first()
        if not assemblage:
            assemblage = FaunalAssemblage(layer=tmp_layer)
            assemblage.save()
            assemblage.refresh_from_db()

        for fam, sp, common, abundance in zip(dat["Family"], dat["Species"], dat["Common Name"], dat["Abundance"]):
            try:
                taxon = Taxon.objects.get(scientific_name=sp, family=fam)
            except:
                taxon = Taxon(scientific_name=sp, common_name=common, family=fam)
                taxon.save()
                taxon.refresh_from_db()
            finally:
                # check if a found taxon is already in...
                create = True
                for found_taxon in assemblage.taxa.all():
                    # if already in: update the abundance
                    if found_taxon.taxon == taxon:
                        found_taxon.abundance = abundance
                        found_taxon.save()
                        create = False
                if create:
                    found_taxon = FoundTaxon(taxon=taxon, abundance=abundance)
                    found_taxon.save()
                    found_taxon.refresh_from_db()
                    assemblage.taxa.add(found_taxon)
        try:
            for ref_id in set([x["id"] for x in dat["Reference"]]):
                reference = Reference.objects.get(id=ref_id)
                assemblage.ref.add(reference)
        except TypeError:  # no reference available
            pass

    return JsonResponse({"status": True})


urlpatterns = [
    path("upload", fauna_upload, name="fauna_upload"),
    path("save", save_verified, name="ajax_save_verified_fauna"),
]
