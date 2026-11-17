## the 3d-view of a sample batch or a site: the samples with X, Y, Z coordinates in their origin (provenience),
## with the results as pie-charts (the overlays of the image viewer)
import json
from django.http import Http404
from django.shortcuts import render
from django.urls import path, reverse
from main.models import SampleBatch, Sample, Site


def coordinate(value):
    """a coordinate of the origin as number (also '12,5'), None if not a number"""
    try:
        return float(str(value).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None


def samples_with_coordinates(request, batch=None, site=None):
    """
    the samples of the batch or the site (with the sample-filters of the DNA tab) that have numeric X, Y and Z in their origin
    """
    from main.tools.samplebatch import filter_samples

    samples = filter_samples(request, Sample.objects.filter(batch=batch) if batch else Sample.objects.filter(site=site)).exclude(provenience=None).exclude(provenience="")
    result = []
    for sample in samples.select_related("layer__culture").prefetch_related("synonyms", "layer__additional_cultures"):
        try:
            origin = {key.strip().lower(): value for key, value in json.loads(sample.provenience).items()}
        except (TypeError, ValueError, AttributeError):
            continue
        xyz = [coordinate(origin.get(axis)) for axis in "xyz"]
        if None not in xyz:
            result.append((sample, xyz))
    return result


def has_coordinates(request, batch=None, site=None):
    return bool(samples_with_coordinates(request, batch=batch, site=site))


def scope(kind, pk):
    """the batch or the site of the 3d-view: (batch, site, title)"""
    if kind == "batch":
        batch = SampleBatch.objects.select_related("site").get(pk=pk)
        return batch, batch.site, f"{batch.site.name}: {batch.name}"
    if kind == "site":
        site = Site.objects.get(pk=pk)
        return None, site, site.name
    raise Http404("unknown scope")


def view3d(request, kind, pk):
    """the 3d-view (modal) of the samples of a batch or a site"""
    from main.tools.analyzed_samples import main_profile
    from main.tools.annotations import sample_data
    from main.models import ProfileLayerJunction

    batch, site, title = scope(kind, pk)
    profile = main_profile(site)
    positions = dict(ProfileLayerJunction.objects.filter(profile=profile).values_list("layer_id", "position")) if profile else {}
    samples = [
        dict(sample_data(sample, positions), x=x, y=y, z=z)
        for sample, (x, y, z) in samples_with_coordinates(request, batch=batch, site=site)
    ]
    return render(request, "main/site/view3d-modal.html", {
        "title": title,
        "samples": json.dumps(samples),
        "overlay_url": reverse("main_view3d_overlay", args=[kind, pk, "OVERLAY"]),
    })


def overlay3d(request, kind, pk, overlay):
    """the results of the samples of the 3d-view: the overlays of the image viewer (quicksand, hominin, clades)"""
    from main.tools import annotations

    overlays = {"quicksand": annotations.quicksand_overlay, "hominin": annotations.hominin_overlay, "clades": annotations.clade_overlay}
    if overlay not in overlays:
        raise Http404("unknown overlay")
    batch, site, title = scope(kind, pk)
    samples = [sample.pk for sample, xyz in samples_with_coordinates(request, batch=batch, site=site)]
    return overlays[overlay](request, None, samples=samples)


urlpatterns = [
    path("<str:kind>/<int:pk>", view3d, name="main_view3d"),
    path("<str:kind>/<int:pk>/<str:overlay>", overlay3d, name="main_view3d_overlay"),
]
