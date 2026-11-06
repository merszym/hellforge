## samples tagged on images (ImageAnnotation): the viewer is the image-modal (image_modal.html, leaflet)
import json
from collections import defaultdict
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q
from django.urls import path
from django.views.decorators.http import require_POST
from main.models import Image, ImageAnnotation, Sample, QuicksandAnalysis


def image_samples(image):
    """
    the samples that can be tagged on an image: the samples of the batch of the gallery
    """
    batch = getattr(image.gallery, "sample_batch", None)
    return Sample.objects.filter(batch=batch) if batch else Sample.objects.none()


def synonym_names(sample):
    return [f"{synonym.type}: {synonym.name}" if synonym.type else synonym.name for synonym in sample.synonyms.all()]


def annotation_data(annotation):
    return {
        "pk": annotation.pk, "sample": annotation.sample_id, "name": annotation.sample.name,
        "synonyms": synonym_names(annotation.sample), "x": annotation.x, "y": annotation.y,
    }


def image_annotations(image):
    """
    the annotations of an image for the viewer (json)
    """
    return json.dumps([annotation_data(a) for a in image.annotations.select_related("sample").prefetch_related("sample__synonyms").order_by("sample__name")])


@login_required
@require_POST
def save_annotation(request, pk):
    """
    tag a sample on the image (or move it): sample and the relative position x, y (0-1)
    """
    image = Image.objects.get(pk=pk)
    try:
        x, y = float(request.POST.get("x")), float(request.POST.get("y"))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("position missing")
    if not (0 <= x <= 1 and 0 <= y <= 1):
        return HttpResponseBadRequest("the position is outside of the image")
    sample = image_samples(image).filter(pk=request.POST.get("sample")).first()
    if sample is None:
        return HttpResponseBadRequest("the sample is not in the batch of the image")
    annotation, created = ImageAnnotation.objects.update_or_create(image=image, sample=sample, defaults={"x": x, "y": y})
    return JsonResponse(annotation_data(annotation), status=201 if created else 200)


@login_required
@require_POST
def delete_annotation(request, pk):
    ImageAnnotation.objects.filter(pk=pk).delete()
    return JsonResponse({"deleted": pk})


def search_samples(request, pk):
    """
    the samples of the batch of the image (type-to-search for tagging, by name or synonym),
    with the synonyms and the information if they are tagged already
    """
    image = Image.objects.get(pk=pk)
    tagged = set(image.annotations.values_list("sample_id", flat=True))
    samples = image_samples(image).order_by("name").prefetch_related("synonyms")
    if query := request.GET.get("q", "").strip():
        samples = samples.filter(Q(name__icontains=query) | Q(synonyms__name__icontains=query)).distinct()
    return JsonResponse(
        [{"pk": s.pk, "name": s.name, "synonyms": synonym_names(s), "tagged": s.pk in tagged} for s in samples[:20]],
        safe=False,
    )


def quicksand_overlay(request, pk):
    """
    the ancient families (quicksand) of the tagged samples, for the pie-charts on the image. per capture-probe:
    {probe: {sample-pk: {family: reads}}}, the reads of several libraries of a sample (same probe) are summed.
    the filters (column, cutoffs, project) are the settings of the quicksand tab, only ancient families
    """
    from main.tools.quicksand import prepare_data
    from main.tools.dna_filters import get_analysis_settings
    from main.tools.analyzed_samples import probe_translations

    image = Image.objects.get(pk=pk)
    query = QuicksandAnalysis.objects.filter(
        analyzedsample__sample__in=image.annotations.values("sample_id")
    ).select_related("analyzedsample")
    settings = get_analysis_settings(request, "quicksand")
    data = prepare_data(
        request,
        query,
        column=settings["column"],
        percentage=settings["percentage"],
        breadth=settings["breadth"],
        ancient=True,
        only_project=settings["only_project"],
    )

    results = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for entry in data["object_list"]:
        library = entry.analyzedsample
        # samples without ancient families are included (empty): analyzed, but negative
        families = results[library.probes or ""][library.sample_id]
        for family, value in data["quicksand_results"].get(entry, {}).items():
            families[family] += value["raw"]

    # the probes with the number of samples with results: the most samples (then the most with families) first
    names = probe_translations()
    probes = sorted(
        results,
        key=lambda probe: (len(results[probe]), sum(1 for families in results[probe].values() if families)),
        reverse=True,
    )
    return JsonResponse({
        "column": data["column"],
        "colors": dict(data["colors"]),
        "probes": [{"value": probe, "name": names.get(probe, probe or "No probes"), "samples": len(results[probe])} for probe in probes],
        "results": results,
    })


urlpatterns = [
    path("image/<int:pk>/save", save_annotation, name="main_annotation_save"),
    path("delete/<int:pk>", delete_annotation, name="main_annotation_delete"),
    path("image/<int:pk>/samples", search_samples, name="main_annotation_samples"),
    path("image/<int:pk>/quicksand", quicksand_overlay, name="main_annotation_quicksand"),
]
