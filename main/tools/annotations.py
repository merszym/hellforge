## samples tagged on images (ImageAnnotation): the viewer is the image-modal (image_modal.html, leaflet)
import json
from collections import defaultdict
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q
from django.urls import path
from django.views.decorators.http import require_POST
from main.models import Image, ImageAnnotation, Sample, QuicksandAnalysis, HumanDiagnosticPositions
from main.tools.matthias import BLACKLISTED_POSITIONS, HOMININ_LINEAGES, SUPPORT


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

    filters = ["is ancient (++)"]
    if settings["percentage"] > 0:
        filters.append(f"has at least {settings['percentage']:g}% of the reads (FamPercentage)")
    if settings["breadth"] > 0:
        filters.append(f"has a breadth of at least {settings['breadth']:g} (ProportionExpectedBreadth)")
    description = (
        f"Pie-charts: the share of each ancient mammalian family in the {data['column']} of quicksand. "
        f"In each library, a family is counted if it {', '.join(filters[:-1]) + ' and ' + filters[-1] if len(filters) > 1 else filters[0]}. "
        "Several libraries of a sample (with the selected capture probe) are merged: the reads of each family are summed. "
        f"Only libraries that passed QC{qc_scope(settings)}. The size of the pie-charts does not depend on the number of reads."
    )
    return JsonResponse({
        "column": data["column"],
        "colors": dict(data["colors"]),
        "probes": sorted_probes(results),
        "results": results,
        "description": description,
    })


# the hominin lineages of the diagnostic positions (AA163 etc.), in this order, with fixed colors
# Neanderthal-related: blues, H(uman): yellow, Denisovan-related: reds, S(ima de los Huesos): green
HOMININ_COLORS = {
    "N": "#1f4e9c", "N-HST": "#4a90d9", "HST": "#9cc8f0",
    "H": "#f5c400",
    "D": "#c62828", "D-S": "#e57373",
    "S": "#2e9e4f",
}
def lineage_support(support):
    """
    the significance marker and the supporting fragments of a lineage, e.g. '^^^54.4% (255 / 469)' -> ('^^^', 255)
    """
    match = SUPPORT.match(str(support or ""))
    return (match.group(1), int(match.group(2))) if match else ("", 0)


def pluralize(items):
    return "s" if len(items) != 1 else ""


def qc_scope(settings):
    return " and are in the project" if settings["only_project"] else ""


def sorted_probes(results):
    """
    the probes with the number of samples with results: the most samples (then the most with a pie-chart) first
    """
    from main.tools.analyzed_samples import probe_translations

    names = probe_translations()
    probes = sorted(
        results,
        key=lambda probe: (len(results[probe]), sum(1 for values in results[probe].values() if values)),
        reverse=True,
    )
    return [{"value": probe, "name": names.get(probe, probe or "No probes"), "samples": len(results[probe])} for probe in probes]


def hominin_overlay(request, pk):
    """
    the hominin mtDNA lineages (diagnostic positions) of the tagged samples, for the pie-charts on the image.
    per capture-probe: {probe: {sample-pk: {lineage: fragments}}} and the states without pie-chart
    {probe: {sample-pk: 'not-ancient' | 'not-significant'}}.
    a library is ancient with '++', a lineage is significant with at least '^^'. the pie-chart: the diagnostic
    fragments of the significant lineages (of the ancient libraries, summed per sample).
    ?mode=deam (default): the deaminated sequences, all: all sequences
    """
    from main.tools.matthias import prepare_data
    from main.tools.dna_filters import get_analysis_settings

    deaminated = request.GET.get("mode", "deam") != "all"
    image = Image.objects.get(pk=pk)
    query = HumanDiagnosticPositions.objects.filter(
        analyzedsample__sample__in=image.annotations.values("sample_id")
    ).select_related("analyzedsample")
    # the filters of the hominin table (qc, project)
    settings = get_analysis_settings(request, "matthias")
    data = prepare_data(request, query, only_project=settings["only_project"])

    results = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    ancient = defaultdict(set)  # probe: the samples with an ancient library
    for entry in data["object_list"]:
        library, values = entry.analyzedsample, data["results"][entry]
        lineages = results[library.probes or ""][library.sample_id]  # analyzed (also if nothing is shown)
        if values.get("Ancient") != "++":
            continue
        ancient[library.probes or ""].add(library.sample_id)
        for lineage in HOMININ_LINEAGES:
            # (prepare_data: already without the blacklisted positions, with the recalculated significance)
            marker, fragments = lineage_support(values.get(f"{lineage}_support{'_deam' if deaminated else ''}"))
            if len(marker) >= 2 and fragments:
                lineages[lineage] += fragments

    states = {
        probe: {
            sample: ("not-significant" if sample in ancient[probe] else "not-ancient")
            for sample, lineages in samples.items() if not lineages
        }
        for probe, samples in results.items()
    }
    sequences = "deaminated sequences" if deaminated else "all sequences"
    blacklisted = ", ".join(str(x) for x in sorted(BLACKLISTED_POSITIONS))
    description = (
        f"Pie-charts: the share of each hominin mtDNA lineage in the diagnostic fragments ({sequences}). "
        "In each library: ancient with '++'; a lineage is counted if its diagnostic test is significant (at least '^^'), "
        "with the fragments that support the lineage at its diagnostic positions"
        f"{f' (position{pluralize(BLACKLISTED_POSITIONS)} {blacklisted} excluded and the significance recalculated without it, as in the summary script: significantly more than 10% support)' if blacklisted else ''}. "
        "Several libraries of a sample (with the selected capture probe) are merged: the fragments of each lineage are "
        "summed over the ancient libraries in which the lineage is significant; the sample is ancient if one of its "
        f"libraries is. Only libraries that passed QC{qc_scope(settings)}. The size of the pie-charts does not depend on the number of fragments."
    )
    return JsonResponse({
        "description": description,
        "column": sequences,
        "colors": HOMININ_COLORS,
        "probes": sorted_probes(results),
        "results": results,
        "states": states,
    })


urlpatterns = [
    path("image/<int:pk>/save", save_annotation, name="main_annotation_save"),
    path("delete/<int:pk>", delete_annotation, name="main_annotation_delete"),
    path("image/<int:pk>/samples", search_samples, name="main_annotation_samples"),
    path("image/<int:pk>/quicksand", quicksand_overlay, name="main_annotation_quicksand"),
    path("image/<int:pk>/hominin", hominin_overlay, name="main_annotation_hominin"),
]
