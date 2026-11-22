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


def layer_positions(image):
    """
    the positions of the layers in the main profile of the site (the order of the layers, as in the DNA tab)
    """
    from main.models import ProfileLayerJunction
    from main.tools.analyzed_samples import main_profile

    batch = getattr(image.gallery, "sample_batch", None)
    if batch is None:
        return {}
    return dict(ProfileLayerJunction.objects.filter(profile=main_profile(batch.site)).values_list("layer_id", "position"))


def sample_data(sample, positions):
    """the sample of a marker (image or 3d-view): name, layer and the culture (colors, order of the legend)"""
    # the layer of origin: the marker is colored by its culture (css-classes of the site page, mixed cultures: layer_<pk>)
    layer = sample.layer
    # the position of the layer (or of its closest parent layer) in the profile: the order of the cultures in the legend
    position = next((positions[pk] for pk in reversed(layer.path_ids) if pk in positions), None) if layer else None
    return {
        "position": position,
        "sample": sample.pk, "name": sample.name,
        "synonyms": synonym_names(sample),
        "layer": layer.name if layer else None,
        "culture": layer.culture.name if layer and layer.culture else None,
        # mixed cultures (the second culture of the layer)
        "mix": next((c.name for c in layer.additional_cultures.all()), None) if layer else None,
        "classes": (f"{layer.culture.classname if layer.culture else 'sterile'} layer_{layer.pk}") if layer else "",
    }


def annotation_data(annotation, positions=None):
    if positions is None:
        positions = layer_positions(annotation.image)
    return dict(sample_data(annotation.sample, positions), pk=annotation.pk, x=annotation.x, y=annotation.y)


def image_annotations(image):
    """
    the annotations of an image for the viewer (json)
    """
    positions = layer_positions(image)
    return json.dumps([annotation_data(a, positions) for a in image.annotations.select_related("sample__layer__culture").prefetch_related("sample__synonyms", "sample__layer__additional_cultures").order_by("sample__name")])


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


def overlay_settings(request, analysis, projects=None):
    """
    the filters of the overlay: the settings of the DNA tab (the libraries of the active project), or for several
    projects (the results map): the global defaults, the numbers can be set in the request (e.g. ?percentage=1),
    the libraries of these projects (settings['projects'])
    """
    from main.tools.dna_filters import get_analysis_settings, ANALYSIS_DEFAULTS

    if projects is None:
        return get_analysis_settings(request, analysis)
    settings = dict(ANALYSIS_DEFAULTS[analysis], only_project=False, projects=projects)
    for key, default in ANALYSIS_DEFAULTS[analysis].items():
        if key in request.GET and isinstance(default, (int, float)) and not isinstance(default, bool):
            try:
                settings[key] = type(default)(float(request.GET[key]))
            except ValueError:
                pass
    return settings


def probe_groups(settings):
    """
    the key of the probe-selection of a library: its capture probe. for several projects (results map): the translation
    of the probe (e.g. 'Human mtDNA' for AA163 and AA22), probes without (unambiguous) translation stay as they are.
    returns (key function, {key: set of the probes}) - the probes of each key are collected when the keys are used
    """
    from main.models import ProbeTranslationTable

    members = defaultdict(set)
    translations = {}
    if settings.get("projects") is not None:
        entries = defaultdict(set)
        for probes, content in ProbeTranslationTable.objects.values_list("probes", "content"):
            entries[probes].add(content)
        translations = {probes: next(iter(contents)) for probes, contents in entries.items() if len(contents) == 1 and next(iter(contents))}

    def key(probes):
        probes = probes or ""
        group = translations.get(probes, probes)
        members[group].add(probes)
        return group

    return key, (members if translations else None)


def in_projects(query, settings, prefix="analyzedsample__"):
    """the results/libraries of the selected projects (results map)"""
    if settings.get("projects") is None:
        return query
    return query.filter(**{f"{prefix}project__in": settings["projects"]}).distinct()


def tagged_samples(pk, samples=None):
    """the samples of the overlay: the samples tagged on the image, or the given samples (e.g. the 3d-view of a site)"""
    return samples if samples is not None else Image.objects.get(pk=pk).annotations.values("sample_id")


def quicksand_overlay(request, pk, samples=None, projects=None):
    """
    the ancient families (quicksand) of the tagged samples, for the pie-charts on the image. per capture-probe:
    {probe: {sample-pk: {family: reads}}}, the reads of several libraries of a sample (same probe) are summed.
    the filters (column, cutoffs, project) are the settings of the quicksand tab, only ancient families
    """
    from main.tools.quicksand import prepare_data

    settings = overlay_settings(request, "quicksand", projects)
    query = in_projects(QuicksandAnalysis.objects.filter(
        analyzedsample__sample__in=tagged_samples(pk, samples)
    ).select_related("analyzedsample"), settings)
    data = prepare_data(
        request,
        query,
        column=settings["column"],
        percentage=settings["percentage"],
        breadth=settings["breadth"],
        ancient=True,
        only_project=settings["only_project"],
    )

    probe_key, probe_members = probe_groups(settings)  # the probe-selection (several projects: by translation)
    results = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for entry in data["object_list"]:
        library = entry.analyzedsample
        # samples without ancient families are included (empty): analyzed, but negative
        families = results[probe_key(library.probes)][library.sample_id]
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
        "probes": sorted_probes(results, probe_members),
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
    if settings.get("projects") is not None:
        return " and are in the selected projects"
    return " and are in the project" if settings["only_project"] else ""


def sorted_probes(results, members=None):
    """
    the probes with the number of samples with results: the most samples (then the most with a pie-chart) first.
    members (probes grouped by their translation): the name is the translation with its probes, e.g. 'Human mtDNA (AA163, AA22)'
    """
    from main.tools.analyzed_samples import probe_translations

    names = probe_translations()
    if members:
        names = {key: f"{key or 'No probes'} ({', '.join(sorted(p or 'no probe' for p in probes))})" if probes != {key} else names.get(key, key or "No probes")
                 for key, probes in members.items()}
    probes = sorted(
        results,
        key=lambda probe: (len(results[probe]), sum(1 for values in results[probe].values() if values)),
        reverse=True,
    )
    return [{"value": probe, "name": names.get(probe, probe or "No probes"), "samples": len(results[probe])} for probe in probes]


def hominin_overlay(request, pk, samples=None, projects=None):
    """
    the hominin mtDNA lineages (diagnostic positions) of the tagged samples, for the pie-charts on the image.
    per capture-probe: {probe: {sample-pk: {lineage: fragments}}} and the states without pie-chart
    {probe: {sample-pk: 'not-ancient' | 'not-significant'}}.
    a library is ancient with '++', a lineage is significant with at least '^^'. the pie-chart: the diagnostic
    fragments of the significant lineages (of the ancient libraries, summed per sample).
    ?mode=deam (default): the deaminated sequences, all: all sequences
    """
    from main.tools.matthias import prepare_data

    deaminated = request.GET.get("mode", "deam") != "all"
    # the filters of the hominin table (qc, project)
    settings = overlay_settings(request, "matthias", projects)
    query = in_projects(HumanDiagnosticPositions.objects.filter(
        analyzedsample__sample__in=tagged_samples(pk, samples)
    ).select_related("analyzedsample"), settings)
    data = prepare_data(request, query, only_project=settings["only_project"])

    probe_key, probe_members = probe_groups(settings)  # the probe-selection (several projects: by translation)
    results = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    ancient = defaultdict(set)  # probe: the samples with an ancient library
    for entry in data["object_list"]:
        library, values = entry.analyzedsample, data["results"][entry]
        lineages = results[probe_key(library.probes)][library.sample_id]  # analyzed (also if nothing is shown)
        if values.get("Ancient") != "++":
            continue
        ancient[probe_key(library.probes)].add(library.sample_id)
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
        "probes": sorted_probes(results, probe_members),
        "results": results,
        "states": states,
    })


def clade_overlay(request, pk, samples=None, projects=None):
    """
    the clades (mammalian per-family analysis) of the tagged samples, for the pie-charts on the image. per family:
    {family: {sample-pk: {clade: est_counts}}}. the filters are the clade settings of the quicksand tab (DNA tab).
    a sample: its merged result (if the result of one of the merged libraries can be seen), otherwise the results
    of its libraries are summed (each library with the filters)
    """
    from main.models import AnalyzedSample, FamilyAnalysis, CladeReference
    from main.tools.clades import filter_clades
    from main.tools.projects import get_project
    from main.tools.quicksand import prepare_data

    samples = tagged_samples(pk, samples)
    settings = overlay_settings(request, "quicksand", projects)
    libraries = in_projects(AnalyzedSample.objects.filter(sample__in=samples, qc_pass=True), settings, prefix="")
    if settings["only_project"]:
        libraries = libraries.filter(project=get_project(request))
    allowed = set(libraries.values_list("pk", flat=True))

    # 'Ancient in quicksand': the families that are ancient in the libraries (with the quicksand cutoffs)
    found = defaultdict(set)
    if settings["cladelinked"]:
        quicksand = prepare_data(
            request, QuicksandAnalysis.objects.filter(analyzedsample__in=libraries).select_related("analyzedsample"),
            column=settings["column"], percentage=settings["percentage"], breadth=settings["breadth"],
            ancient=True, only_project=settings["only_project"],
        )
        for entry, families in quicksand["quicksand_results"].items():
            found[entry.analyzedsample_id].update(families)

    groups = defaultdict(list)  # (family, sample): the results
    query = FamilyAnalysis.objects.filter(Q(sample__in=samples) | Q(analyzedsample__sample__in=samples)) \
        .select_related("analyzedsample").prefetch_related("libraries")
    for analysis in query:
        libs = [analysis.analyzedsample_id] if analysis.analyzedsample_id else [l.pk for l in analysis.libraries.all()]
        libs = [lib for lib in libs if lib in allowed]
        if libs:
            groups[(analysis.family, analysis.sample_id or analysis.analyzedsample.sample_id)].append((analysis, libs))

    references = {family: CladeReference.latest(family) for family in {family for family, sample in groups}}
    results = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    for (family, sample), entries in groups.items():
        merged = [entry for entry in entries if entry[0].sample_id]
        clades = results[family][sample]  # analyzed (also if nothing is shown)
        for analysis, libs in merged[:1] or entries:
            if settings["cladelinked"] and not any(family in found[lib] for lib in libs):
                continue
            valid, counts, total, sink = filter_clades(analysis, references[family], settings)
            for clade, n in counts.items():
                clades[clade] += n
    for family in results:
        for sample in results[family]:
            results[family][sample] = {clade: round(n, 1) for clade, n in results[family][sample].items()}

    colors, order = {}, []
    for reference in references.values():
        colors.update((reference.color_palette or {}) if reference else {})
        order += reference.clade_order() if reference else []
    filters = [f"at least {settings['clademinseqs']} unique sequences (pseudoaligned)",
               f"less than {settings['cladesinkratio']:g} estimated counts in the sink (unassigned genomes) per estimated count with clade"]
    if settings["cladelinked"]:
        filters.append("the family ancient (++) in quicksand")
    description = (
        "Pie-charts: the share of each clade of the selected family in the estimated counts (kallisto, summed per clade). "
        f"A result is used if it has {', '.join(filters[:-1])} and {filters[-1]}; "
        f"a clade is counted with at least {settings['clademincounts']:g} estimated counts and {settings['cladepercent']:g}% of the estimated counts with clade. "
        "The merged result of a sample is used if there is one, otherwise the clades of its libraries are summed. "
        f"Only libraries that passed QC{qc_scope(settings)}. The size of the pie-charts does not depend on the estimated counts."
    )
    return JsonResponse({
        "column": "estimated counts",
        "colors": colors,
        "order": order,  # the clades in the order of the references (pies, legend), otherwise by value
        "probes": sorted_probes(results),
        "results": results,
        "description": description,
    })


urlpatterns = [
    path("image/<int:pk>/save", save_annotation, name="main_annotation_save"),
    path("delete/<int:pk>", delete_annotation, name="main_annotation_delete"),
    path("image/<int:pk>/samples", search_samples, name="main_annotation_samples"),
    path("image/<int:pk>/quicksand", quicksand_overlay, name="main_annotation_quicksand"),
    path("image/<int:pk>/hominin", hominin_overlay, name="main_annotation_hominin"),
    path("image/<int:pk>/clades", clade_overlay, name="main_annotation_clades"),
]
