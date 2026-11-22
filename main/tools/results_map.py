## the results map: the dated samples of the selected projects on a timeline (by country), the samples in the selected
## time window on the map (one marker per site, the results of its samples merged, as in the image overlays).
## the same view on its own page (all projects that can be seen) and in the project page (the project selected).
## the samples are loaded per project (the page keeps them), the results for the selected projects and cutoffs
import json
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.db.models import Q
from django.urls import path, reverse
from main.models import Project, Sample


def permitted_projects(request):
    """logged in: all projects, else the published projects and the project of the session (opened with its link)"""
    from main.tools.projects import get_project

    if request.user.is_authenticated:
        return Project.objects.all()
    projects = Project.objects.filter(published=True)
    if session_project := get_project(request):
        projects = projects | Project.objects.filter(pk=session_project.pk)
    return projects.distinct()


def requested_projects(request):
    """the selected projects (?projects=1,2) that can be seen"""
    pks = [int(x) for x in request.GET.get("projects", "").split(",") if x.strip().isdigit()]
    return list(permitted_projects(request).filter(pk__in=pks).values_list("pk", flat=True))


def site_point(site):
    """(lat, lon) of the site: the point of its first location (a polygon: the mean of its corners), else None"""
    location = next(iter(site.loc.all()), None)
    if location is None or not location.geo:
        return None
    geo = location.geo
    try:
        geo = json.loads(geo) if isinstance(geo, str) else geo
        geometry = geo["features"][0]["geometry"]
        coordinates = geometry["coordinates"]
        if geometry["type"] == "Point":
            lon, lat = coordinates[:2]
        else:  # polygon: the mean of the corners of the outer ring
            ring = coordinates[0] if geometry["type"] == "Polygon" else coordinates[0][0]
            lon, lat = sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring)
        return float(lat), float(lon)
    except (KeyError, IndexError, TypeError, ValueError, ZeroDivisionError):
        return None


def sample_age(sample):
    """
    (upper, lower, infinite) of the sample in years: its own age, else the age of the layer (as in the export).
    infinite ages (beyond the dating limit): upper == lower, the point estimate. None if not dated
    """
    infinite, upper, lower = sample.get_upper_and_lower(calculate_mean=True)
    if upper is None and lower is None and sample.layer:
        infinite, upper, lower = sample.layer.get_upper_and_lower(calculate_mean=True)
    if upper is None and lower is None:
        return None
    if infinite:
        point = upper if upper is not None else lower
        return point, point, True
    upper, lower = upper if upper is not None else lower, lower if lower is not None else upper
    return max(upper, lower), min(upper, lower), False


# the cutoffs that can be changed in the view (the global defaults): (setting, label, results)
CUTOFFS = [
    ("percentage", "Percentage", "quicksand"),
    ("breadth", "Breadth", "quicksand"),
    ("cladepercent", "Clade %", "clades"),
    ("clademinseqs", "Min. unique seqs.", "clades"),
    ("clademincounts", "Min. counts per clade", "clades"),
    ("cladesinkratio", "Max. sink / clade counts", "clades"),
]


def results_map(request):
    """the view: on its own page, or (?project=<pk>, ?embed) in the project page with the project selected"""
    from main.tools.dna_filters import ANALYSIS_DEFAULTS

    # the published projects first (by year of publication, shown by their reference), then the others by name
    def label(project):
        ref = next(iter(project.ref.all()), None)
        return (ref.parsedInline or ref.short or project.name) if (project.published and ref) else project.name
    # only projects with results (quicksand, hominin mtDNA, clades of libraries in the project);
    # the project of the project page is always shown
    selected = request.GET.get("project", "")
    with_results = Q(analyzedsample__quicksand_analysis__isnull=False) | Q(analyzedsample__matthias_analysis__isnull=False) | \
        Q(analyzedsample__family_analysis__isnull=False) | Q(analyzedsample__merged_family_analysis__isnull=False)
    if selected.isdigit():
        with_results |= Q(pk=int(selected))
    projects = permitted_projects(request).filter(pk__in=Project.objects.filter(with_results).values("pk")).prefetch_related("ref")
    # published: by year of publication (without year: last), then by the reference
    projects = sorted(projects, key=lambda p: (not p.published, p.year_of_publication or 9999 if p.published else 0, label(p).lower()))
    context = {
        "projects": projects,
        "selected": [int(selected)] if selected.isdigit() and int(selected) in {p.pk for p in projects} else [],
        "embed": "embed" in request.GET,
        "cutoffs": [(key, label, ANALYSIS_DEFAULTS["quicksand"][key], analyses) for key, label, analyses in CUTOFFS],
    }
    template = "main/results_map/results-map.html" if context["embed"] else "main/results_map/results-map-page.html"
    return render(request, template, context)


def project_samples(request, pk):
    """the dated samples of a project (with their site and age) and their sites (with their position)"""
    project = permitted_projects(request).filter(pk=pk).first()
    if project is None:
        raise Http404("unknown project")
    samples = Sample.objects.filter(project=project, domain="mpi_eva").select_related("site", "layer", "sample").prefetch_related("site__loc")
    sites, rows, positions = {}, [], {}
    for sample in samples:
        if sample.site_id is None:
            continue
        if sample.site_id not in positions:
            positions[sample.site_id] = site_point(sample.site)
        if positions[sample.site_id] is None or (age := sample_age(sample)) is None:
            continue
        sites.setdefault(sample.site_id, {
            "pk": sample.site_id, "name": sample.site.name, "country": sample.site.country or "Unknown",
            "lat": positions[sample.site_id][0], "lon": positions[sample.site_id][1],
            "url": reverse("site_detail", args=[sample.site_id]),
        })
        rows.append({"sample": sample.pk, "name": sample.name, "site": sample.site_id,
                     "upper": age[0], "lower": age[1], "infinite": age[2], "layer": sample.layer.name if sample.layer else None})
    return JsonResponse({"samples": rows, "sites": sites})


def overlay(request, overlay):
    """
    the results of the samples of the selected projects (the overlays of the image viewer): the libraries of these
    projects, with the global cutoffs (set in the request)
    """
    from main.tools import annotations

    overlays = {"quicksand": annotations.quicksand_overlay, "hominin": annotations.hominin_overlay, "clades": annotations.clade_overlay}
    if overlay not in overlays:
        raise Http404("unknown overlay")
    projects = requested_projects(request)
    samples = Sample.objects.filter(project__in=projects, domain="mpi_eva").values("pk")
    return overlays[overlay](request, None, samples=samples, projects=projects)


urlpatterns = [
    path("", results_map, name="main_results_map"),
    path("samples/<int:pk>", project_samples, name="main_results_map_samples"),
    path("overlay/<str:overlay>", overlay, name="main_results_map_overlay"),
]
