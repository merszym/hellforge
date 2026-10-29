## the filters of the DNA tab (site detail): one state for the samples, libraries and analyses
#
# the side-panel posts the changed fields, the state is kept in the session and the parts of the tab
# that depend on the changed level reload (see site-sample-content.html):
#   samples -> batches, libraries, analyses
#   libraries -> libraries, analyses
#   quicksand/matthias/nedflow -> only this analysis
# the sample- and library-filters use the session-keys that are read by filter_samples and filter_libraries
import json
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.urls import path
from django.views.decorators.http import require_POST
from django.db.models import Q
from main.models import Site, Layer, Culture, Sample, SampleBatch, AnalyzedSample, ProjectTag
from main.tools.generic import get_instance_from_string
from main.tools.projects import get_project


# field in the filter-form -> session-keys (the first one holds the value)
SAMPLE_FIELDS = {
    "layer": ["filter_layer_pk", "filter_layer_name"],
    "culture": ["filter_culture"],
    "batch": ["filter_batch_pk", "filter_batch_name"],
    "no_layer": ["filter_no_layer"],
    "analyzed": ["filter_analyzed"],
    "combine": ["filter_combine"],
}
LIBRARY_FIELDS = {
    "search": ["filter_search"],
    "probe": ["filter_probe"],
    "controls": ["filter_controls"],
    "missing": ["filter_missing"],
    "project_tag": ["filter_project_tags"],
    # not a filter: the order of the libraries and analysis results (set in the table-headers)
    "sort": ["filter_sort"],
}
# the filters for admins only (logged-in users)
ADMIN_FIELDS = ["no_layer", "missing"]

# the settings of the analysis tables, the fields in the form are prefixed (e.g. qs_ancient)
ANALYSIS_PREFIX = {"quicksand": "qs", "matthias": "mm", "nedflow": "ned"}
ANALYSIS_NAMES = {"quicksand": "Mammalian mtDNA", "matthias": "Hominin mtDNA", "nedflow": "Nuclear DNA"}
ANALYSIS_DEFAULTS = {
    "quicksand": {
        "column": "ReadsDeduped", "percentage": 0.5, "breadth": 0.5, "ancient": True,
        "positives": False, "tableview": False, "only_project": True, "family": [],
    },
    "matthias": {"ancient": True, "positives": False, "extended": False, "only_project": True},
    "nedflow": {"ancient": "++", "fampercent": 1.0, "positives": False, "only_project": True, "family": []},
}

# rows per page of the analysis tables
DEFAULT_PAGE_SIZE = 300

SAMPLE_KEYS = [key for keys in SAMPLE_FIELDS.values() for key in keys]
LIBRARY_KEYS = [key for keys in LIBRARY_FIELDS.values() for key in keys]
ALL_KEYS = SAMPLE_KEYS + LIBRARY_KEYS + ["filter_analyses"]


def reset_dna_filters(request, section="all"):
    """
    reset the filters of a section of the DNA tab (samples, libraries, results) or all
    """
    keys = {"samples": SAMPLE_KEYS, "libraries": LIBRARY_KEYS, "results": ["filter_analyses"]}.get(section, ALL_KEYS)
    for key in keys:
        request.session.pop(key, None)


def analysis_defaults(request, analysis):
    """
    the default settings of an analysis table (quicksand cutoffs are set in the project)
    """
    settings = dict(ANALYSIS_DEFAULTS[analysis])
    if analysis == "quicksand":
        project = get_project(request)
        if project and project.parameters:
            params = json.loads(project.parameters)
            settings["percentage"] = float(params.get("quicksand_cutoff_percentage", settings["percentage"]))
            settings["breadth"] = float(params.get("quicksand_cutoff_breadth", settings["breadth"]))
    return settings


def get_analysis_settings(request, analysis):
    """
    the current settings of an analysis table
    """
    settings = analysis_defaults(request, analysis)
    settings.update(request.session.get("filter_analyses", {}).get(analysis, {}))
    # only logged-in users can see results of libraries outside of the project
    if not request.user.is_authenticated:
        settings["only_project"] = True
    return settings


def get_per_page(request):
    return DEFAULT_PAGE_SIZE


def filter_state(request):
    """
    the current state of all filters, to find out what changed
    """
    state = {key: request.session.get(key) for key in ALL_KEYS}
    state["filter_analyses"] = json.dumps(request.session.get("filter_analyses", {}), sort_keys=True)
    return state


def changed_levels(before, after):
    levels = set()
    if any(before[key] != after[key] for key in SAMPLE_KEYS):
        levels.add("samples")
    if any(before[key] != after[key] for key in LIBRARY_KEYS):
        levels.add("libraries")
    old = json.loads(before["filter_analyses"])
    new = json.loads(after["filter_analyses"])
    for analysis in ANALYSIS_DEFAULTS:
        if old.get(analysis) != new.get(analysis):
            levels.add(analysis)
    return levels


def set_instance_filter(request, keys, value):
    """
    filters that select an object ('all' or e.g. 'layer_12'): save pk and name
    """
    for key in keys:
        request.session.pop(key, None)
    if value and value != "all":
        instance = get_instance_from_string(value)
        request.session[keys[0]] = instance.pk
        request.session[keys[1]] = instance.name


def set_filter(request, field):
    """
    save the posted value of a field of the filter-form in the session
    """
    post = request.POST
    if field in ADMIN_FIELDS and not request.user.is_authenticated:
        return
    if field in ("layer", "batch"):
        set_instance_filter(request, SAMPLE_FIELDS[field], post.get(field, "all"))
    elif field == "culture":
        # culture pks and 'sterile' (several can be selected)
        cultures = [int(x) if x.isdigit() else x for x in post.getlist("culture") if x.isdigit() or x == "sterile"]
        if cultures:
            request.session["filter_culture"] = cultures
        else:
            request.session.pop("filter_culture", None)
    elif field in ("analyzed", "combine", "no_layer"):
        request.session[SAMPLE_FIELDS[field][0]] = field in post
    elif field == "controls":
        request.session["filter_controls"] = field in post
    elif field == "search":
        search = post.get("search", "").strip()
        if search:
            request.session["filter_search"] = search
        else:
            request.session.pop("filter_search", None)
    elif field == "sort":
        from main.tools.analyzed_samples import LIBRARY_SORTS
        if post.get("sort") in LIBRARY_SORTS:
            request.session["filter_sort"] = post.get("sort")
    elif field == "project_tag":
        # the project-tags (pks, several can be selected)
        tags = [int(x) for x in post.getlist("project_tag") if x.isdigit()]
        if tags:
            request.session["filter_project_tags"] = tags
        else:
            request.session.pop("filter_project_tags", None)
    elif field == "missing":
        # libraries without results in any of these analyses
        missing = [x for x in post.getlist("missing") if x in ANALYSIS_DEFAULTS]
        if missing:
            request.session["filter_missing"] = missing
        else:
            request.session.pop("filter_missing", None)
    elif field == "probe":
        probes = [x for x in post.getlist("probe") if x and x != "all"]
        if probes:
            request.session["filter_probe"] = probes
        else:
            request.session.pop("filter_probe", None)
    else:
        # the settings of the analysis tables, e.g. qs_ancient
        prefix, _, name = field.partition("_")
        analysis = {v: k for k, v in ANALYSIS_PREFIX.items()}.get(prefix)
        if not analysis or name not in ANALYSIS_DEFAULTS[analysis]:
            return
        default = ANALYSIS_DEFAULTS[analysis][name]
        if isinstance(default, bool):
            value = field in post
        elif isinstance(default, list):
            value = post.getlist(field)
        elif isinstance(default, float):
            try:
                value = float(post.get(field, default))
            except ValueError:
                return
        else:
            value = post.get(field, "").strip()
        analyses = request.session.get("filter_analyses", {})
        analyses.setdefault(analysis, {})[name] = value
        request.session["filter_analyses"] = analyses


def active_filters(request):
    """
    the labels of the active filters per section, for the chips above the sections
    """
    session = request.session
    samples, libraries, results = [], [], []
    if session.get("filter_layer_pk"):
        samples.append(f"Layer: {session['filter_layer_name']}")
    if session.get("filter_culture"):
        names = dict(Culture.objects.filter(pk__in=[x for x in session["filter_culture"] if x != "sterile"]).values_list("pk", "name"))
        labels = [names.get(x, "Sterile" if x == "sterile" else str(x)) for x in session["filter_culture"]]
        samples.append(f"Cultures: {', '.join(labels)}")
    if session.get("filter_batch_pk"):
        samples.append(f"Batch: {session['filter_batch_name']}")
    if session.get("filter_no_layer") and request.user.is_authenticated:
        samples.append("No layer")
    if session.get("filter_analyzed"):
        samples.append("Analyzed samples only")
    if session.get("filter_combine"):
        samples.append("Batches combined")
    if session.get("filter_search"):
        libraries.append(f"Search: {session['filter_search']}")
    if session.get("filter_probe"):
        libraries.append(f"Probes: {', '.join(session['filter_probe'])}")
    if session.get("filter_project_tags"):
        names = ProjectTag.objects.filter(pk__in=session["filter_project_tags"], project=get_project(request)).values_list("name", flat=True)
        if names:
            libraries.append(f"Tags: {', '.join(names)}")
    if session.get("filter_controls"):
        libraries.append("No controls")
    if session.get("filter_missing") and request.user.is_authenticated:
        libraries.append(f"Missing: {', '.join(ANALYSIS_NAMES[x] for x in session['filter_missing'])}")

    # the analysis settings that differ from the defaults
    texts = {
        "column": lambda v: f"Values: {v}",
        "percentage": lambda v: f"Percentage ≥ {v}",
        "breadth": lambda v: f"Breadth ≥ {v}",
        "fampercent": lambda v: f"Percentage ≥ {v}",
        "ancient": lambda v: ("Ancientness: " + (v or "any")) if isinstance(v, str) else ("Ancient only" if v else "Not only ancient"),
        "positives": lambda v: "Any family" if v else None,
        "tableview": lambda v: "Table-View" if v else None,
        "extended": lambda v: "Extended" if v else None,
        "only_project": lambda v: "In project" if v else "All projects",
        "family": lambda v: f"Families: {', '.join(v)}" if v else None,
    }
    for analysis in ANALYSIS_DEFAULTS:
        defaults = analysis_defaults(request, analysis)
        settings = get_analysis_settings(request, analysis)
        for name, value in settings.items():
            if value != defaults[name] and (text := texts[name](value)):
                results.append(f"{ANALYSIS_NAMES[analysis]}: {text}")
    return {"samples": samples, "libraries": libraries, "results": results}


def filter_context(request, site):
    """
    the active filters per section, for the chips above the sections of the DNA tab
    """
    active = active_filters(request)
    return {
        "object": site,
        "active_filters": active,
        "active_count": sum(len(labels) for labels in active.values()),
    }


def panel_context(request, site):
    """
    the options of the filter side-panel (all options of the site, independent of the other filters)
    """
    project = get_project(request)
    libraries = AnalyzedSample.objects.filter(sample__site=site)
    if not request.user.is_authenticated:
        libraries = libraries.filter(project=project, qc_pass=True)
    # only the cultures with samples (as in filter_samples: the culture of the own layer or of the parent sample)
    samples = Sample.objects.filter(site=site).order_by()
    if not request.user.is_authenticated:
        samples = samples.filter(project=project)
    culture_ids = set(samples.values_list("layer__culture", flat=True))
    # samples without a culture (see the 'sterile' filter in filter_samples)
    has_sterile = samples.filter(layer__culture__isnull=True).exists()
    # the layers with samples (that can be seen) and their parent layers (from the path)
    layer_samples = samples if not request.user.is_authenticated else Sample.objects.filter(layer__site=site)
    layer_ids = {int(x) for path in layer_samples.exclude(layer=None).values_list("layer__path", flat=True).distinct() for x in path.strip("/").split("/")}
    layers = Layer.objects.filter(site=site, pk__in=layer_ids)
    return {
        "object": site,
        "layers": layers,
        "cultures": Culture.objects.filter(pk__in=culture_ids - {None}),
        "has_sterile": has_sterile,
        "selected_cultures": request.session.get("filter_culture", []),
        "missing_options": [(analysis, ANALYSIS_NAMES[analysis]) for analysis in ANALYSIS_DEFAULTS],
        # the tags of the active project, that are used by libraries of the site
        "project_tags": ProjectTag.objects.filter(project=project, analyzedsamples__sample__site=site).distinct(),
        "selected_project_tags": request.session.get("filter_project_tags", []),
        "selected_missing": request.session.get("filter_missing", []),
        # only the batches of samples that can be seen (not logged in: the samples of the project)
        "sample_batches": SampleBatch.objects.filter(sample__in=samples.filter(domain="mpi_eva")).distinct().order_by("name"),
        "probes": sorted(libraries.exclude(probes=None).order_by().values_list("probes", flat=True).distinct()),
        "analyses": [
            (analysis, ANALYSIS_NAMES[analysis], ANALYSIS_PREFIX[analysis], get_analysis_settings(request, analysis))
            for analysis in ANALYSIS_DEFAULTS
        ],
    }


@require_POST
def update_dna_filters(request, pk):
    """
    save the posted fields of the filter-form (or reset filters, reset=all/samples/libraries/results).
    returns the active-filter chips, and triggers the reload of the changed parts of the tab
    """
    site = Site.objects.filter(pk=pk).first()
    if not site:
        return HttpResponseBadRequest("unknown site")

    before = filter_state(request)
    if reset := request.POST.get("reset"):
        reset_dna_filters(request, reset)
    else:
        # only the fields that are listed are updated, the others keep their value
        for field in request.POST.getlist("_fields"):
            set_filter(request, field)
    levels = changed_levels(before, filter_state(request))

    context = filter_context(request, site)
    # the panel shows the new values if they were not set in the panel (e.g. reset)
    if reset or not request.POST.get("_from_panel"):
        context.update(panel_context(request, site))
        context["refresh_panel"] = True
    response = render(request, "main/site/dna-active-filters.html", context)
    if levels:
        response["HX-Trigger"] = json.dumps({"dna-filter-changed": {"levels": sorted(levels)}})
    return response


urlpatterns = [
    path("<int:pk>/update", update_dna_filters, name="main_dna_filters_update"),
]
