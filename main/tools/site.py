from django.urls import path, reverse
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import CreateView, ListView, UpdateView, DetailView
from django.db.models import Q, Count
from django.core.paginator import Paginator
from main.forms import ProfileForm, SiteForm, SampleBatchForm
from main.models import (
    Site,
    Location,
    Culture,
    Profile,
    Layer,
    Date,
    Description,
    Project,
    Sample,
    SampleBatch,
    AnalyzedSample,
    Gallery,
    Synonym,
    Connection,
    QuicksandAnalysis,
    HumanDiagnosticPositions,
    ProfileLayerJunction,
    Reference
)
from copy import copy
import json
import seaborn as sns
import pandas as pd
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)  # this is for now, make smarter later
from django.contrib.auth.decorators import (
    login_required,
)  # this is for now, make smarter later
from collections import defaultdict
from django.shortcuts import get_object_or_404
from main.views import ProjectAwareListView, ProjectAwareDetailView
from main.tools.generic import (
    add_x_to_y_m2m,
    remove_x_from_y_m2m,
    get_instance_from_string,
)
from main.tools.projects import get_project
from main.tools.quicksand import prepare_data
from main.tools.analyzed_samples import update_query_for_negatives
from main.tools.profile import layers_for_table, attach_highest_layers


## Sites
class SiteDetailView(ProjectAwareDetailView):
    model = Site
    template_name = "main/site/site_detail.html"

    def get_context_data(self, **kwargs):
        context = super(SiteDetailView, self).get_context_data(**kwargs)
        tab = self.request.GET.get("tab", "site_layer")
        object = self.get_object()

        # get the project description
        try:
            project_description = Description.objects.get(
                project=context.get("project"), site=object
            )
        except:
            project_description = None

        context.update(
            {
                "project_description": project_description,
                "tab": tab,
            }
        )

        return context


class SiteListView(ProjectAwareListView):
    model = Site
    template_name = "main/site/site_list.html"

    def get_queryset(self, **kwargs):
        queryset = super(SiteListView, self).get_queryset(**kwargs)
        return queryset.filter(child=None)


def get_culture_css(request, site_id):
    site = Site.objects.get(pk=site_id)
    # cultures are loaded in bulk (additional_cultures.first() below uses the prefetched, ordered list)
    layers = Layer.objects.filter(Q(site=site)).select_related("culture").prefetch_related("additional_cultures")

    cultures = {}
    context = {}
    for n, cult in enumerate(
        Culture.objects.filter(
            Q(layer__in=layers) 
            | Q(layers__in=layers)
            | Q(layer_analysis__site__layer__in=layers)
        ).order_by("layer__profile_junction__position")
    ):
        cultures[cult.classname] = n

    cult_color_dict = {
        k:v for k,v in zip(
            [x for x in sorted(cultures, key=lambda x: cultures[x])],
            sns.color_palette("husl", len(cultures)).as_hex(),
        )
    }

    context["cultures"] = cult_color_dict.items()

    #for mixed cultures, create a gradient
    mixed = {}
    for layer in layers:
        if mix:= layer.additional_cultures.first():
            mixed[f"layer_{layer.pk}"] = (cult_color_dict[layer.culture.classname], cult_color_dict[mix.classname])

    context['mixed'] = mixed.items()
    return render(request, "main/site/site_culture_css.html", context)


def get_timeline_data(site_id, request=False, profile=None):
    project = get_project(request) if request else None
    data = {}
    site = Site.objects.get(pk=site_id)

    if profile:
        layers = Layer.objects.filter(
            Q(site=site) & Q(profile_junction__profile=profile)
        )
    else:
        layers = Layer.objects.filter(Q(site=site))
    # everything that is displayed, in bulk instead of per layer/date
    layers = layers.select_related("culture", "date_upper", "date_lower").prefetch_related(
        "date__ref",
        "date__layer_model",
        "sample__date__ref",
        "sample__date__layer_model",
        "sample__date__sample_model",
    )

    # the position of the layers in the profile (without a profile: the first position in any profile)
    junctions = ProfileLayerJunction.objects.filter(layer__in=layers)
    if profile:
        junctions = junctions.filter(profile=profile)
    positions = {}
    for layer_id, position in junctions.values_list("layer_id", "position"):
        positions.setdefault(layer_id, position)

    # these are the same for all layers
    in_project = bool(project) and project.site.filter(pk=site.pk).exists()
    authenticated = request.user.is_authenticated

    unique_groups = set(layers)
    groups = [
        {
            "id": layer.name.lower(),
            "content": layer.name,
            "treeLevel": 2,
            "order": positions.get(layer.pk, 0),
        }
        for layer in unique_groups
    ]
    dates = []
    for layer in layers:
        background = {}

        infinite, upper, lower = layer.get_upper_and_lower()
        if infinite:
            upper = upper + 5000  # for display purposes

        if upper and lower:
            bg_date = Date(upper=upper, lower=lower)
            # convert to ms
            sup, slo = bg_date.to_ms()
            background.update(
                {
                    "hierarchy": "2" if (layer.date_upper or layer.date_lower) else "1",
                    "start": sup,
                    "end": slo,
                    "order": sup * -1,
                    "content": f"{layer.age_summary()}",
                    "group": layer.name.lower(),
                    "type": "background",
                    "background": True,
                    "className": "infinite" if infinite else "",
                }
            )

        if len(background) > 0:
            dates.append(background)
        # now for the dates
        if in_project or authenticated:
            tmp_dates = list(layer.date.all())
        else:
            # if not in project and view-only dont display unpublished dates
            tmp_dates = [x for x in list(layer.date.all()) if len(x.ref.all()) > 0]

        # now add the dates from the samples that are NOT also in the layers
        sample_dates = [
            date
            for sample in layer.sample.all()
            for date in sample.date.all()
            if len(date.layer_model.all()) == 0
        ]

        if not in_project or not authenticated:
            sample_dates = [x for x in sample_dates if len(x.ref.all()) > 0]

        # same order as the Date model
        tmp_dates.extend(sorted(sample_dates, key=lambda x: (x.upper is not None, x.upper or 0)))

        for date in tmp_dates:
            try:
                content = [f"{date}"]
            except:
                content = ["test"]
            if len(date.layer_model.all()) == 0:
                content.append(f"({date.sample_model.first().name})")
            upper, lower = date.to_ms()
            layerdata = {
                "start": upper,
                "order": upper * -1,
                "content": "<br>".join(content),
                "group": layer.name.lower(),
                "className": layer.culture.classname if layer.culture else "sterile",
                "type": "point",
                "style": f"{'background-color: rgba(0,0,0,0); border: none;' if date.raw else ''}",
                "usesvg": True if date.raw else False,
                "polygon": f"{date.get_polygon_css() if date.raw else ''}",
                "oxa": f"{date.oxa if date.oxa else ''}",
                "method": date.method,
                "background": False,
            }

            # if range instead of point
            if upper != lower:
                layerdata.update({"end": lower, "type": "range"})

            # if date has only lower (beyond radiocarbon) -> to_ms() returns False, False
            if not any([upper, lower]):
                upper, lower = Date(lower=date.lower, upper=date.lower).to_ms()
                layerdata.update({"start": lower, "end": lower, "type": "point"})

            dates.append(layerdata)
    data["groups"] = json.dumps(groups)
    data["itemdata"] = json.dumps(dates)
    return data


## Profiles


@login_required
def add_profile(request, site_id):
    """
    create and add a new profile within a Site
    """
    site = Site.objects.get(pk=site_id)
    form = ProfileForm(request.POST)
    if form.is_valid():
        profile = form.save(commit=False)
        profile.site = site
        profile.save()
    return redirect(site)


def get_site_profile_tab(request):
    object = get_instance_from_string(request.GET.get("site"))
    if selected_profile := request.GET.get("profile", False):
        selected_profile = get_instance_from_string(selected_profile)
    else:
        selected_profile = object.profile.first()
    
    from django.db.models import Case, When, Value, IntegerField

    profiles = (
        object.profile.all()
        .annotate(
            main_first=Case(
                When(name="Main Profile", then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by("main_first", "name")
    )

    # get the project context
    project = get_project(request)
        
    context = {
        "object": object,
        "selected_profile": selected_profile,
        "profiles":profiles,
        "project_sites": list(project.site.values_list('pk', flat=True)) if project else []
    }

    return render(request, "main/site/site-profile-content.html", context)


@login_required
def get_site_other_layers(request):
    """
    all layers of the site, to add them to the selected profile (stratigraphy tab, loaded when opened)
    """
    object = get_instance_from_string(request.GET.get("site"))
    if profile := request.GET.get("profile"):
        selected_profile = get_instance_from_string(profile)
    else:
        selected_profile = object.profile.first()

    context = {
        "object": object,
        "selected_profile": selected_profile,
        "layers": attach_highest_layers(layers_for_table(object.layer.all())),
    }
    return render(request, "main/profile/other-layers.html", context)


@login_required
def site_create_update(request, pk=None):
    object = Site.objects.get(pk=pk) if pk else None
    if request.method == "POST":
        form = SiteForm(request.POST, instance=copy(object))
        if form.is_valid():
            obj = form.save()
            description = Description(content_object=obj)
            description.save()
            # update the location
            lat = form.cleaned_data.get("lat")
            long = form.cleaned_data.get("long")
            if lat and long:
                geo = {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {},
                            "geometry": {"type": "Point", "coordinates": [long, lat]},
                        }
                    ],
                }
                if not obj.loc.first():
                    loc = Location.objects.create(
                        geo=json.dumps(geo), name=f"{obj.name} Location"
                    )
                    obj.loc.add(loc)
                else:
                    loc = obj.loc.first()
                    loc.geo = json.dumps(geo)
                    loc.save()
            return redirect(obj)
        return render(
            request, "main/site/site_form.html", {"object": object, "form": form}
        )
    return render(
        request,
        "main/site/site_form.html",
        {
            "form": SiteForm(instance=copy(object)),
            "object": object,
            "parent_options": Site.objects.all(),
        },
    )


def get_site_element(request):
    object = Site.objects.get(pk=int(request.GET.get("object")))
    element = request.GET.get("element")
    project = get_project(request)
    return render(
        request,
        "main/site/site_elements.html",
        {"object": object, "element": element, "project": project},
    )


def get_site_geo(request):
    locations = []
    project = get_project(request)
    if request.GET.get("all", False) == "1":
        for site in Site.objects.all():
            if (
                site.visible
                or request.user.is_authenticated
                or (site in Site.objects.filter(project=project) and project == project)
            ):
                locations.append(site.get_location_features())
    else:
        object = Site.objects.get(pk=int(request.GET.get("object")))
        if object.child.all():
            # if this is an umbrella site
            for child in object.child.all():
                locations.append(child.get_location_features())
        else:
            locations.append(object.get_location_features())
    locations = [x for x in locations if x != {}]
    return JsonResponse(locations, safe=False)


# Site Sample Tab
## Main sample-content

def get_site_sample_content(request):
    """
    the DNA tab: the filter side-panel and the (separately loaded) batches, libraries and analyses
    """
    from main.tools.dna_filters import reset_dna_filters, panel_context, filter_context

    if request.method == 'POST':
        try:
            object = Site.objects.get(pk=int(request.POST.get("object")))
        except:
            object = get_instance_from_string(request.POST.get('object'))
    else:
        object = get_instance_from_string(request.GET.get("object"))
    
    
    # If no project is selected, display the available public projects that contain the site
    project = get_project(request)
    if project == None or object not in project.site.all():
        # get the projects
        projects = Project.objects.filter(Q(published=True)&Q(site=object))
        return render(request, "main/project/public_projects_snippet.html", {'public_projects':projects, 'site_view':True, 'object':object})

    # a new page starts without filters
    # (POST: e.g. after adding a batch, keep the filters)
    if request.method == 'GET':
        reset_dna_filters(request)

    # first create a batch for the samples that dont have one yet...
    # only write if necessary: samples without a batch, or no batch at all (needed to upload samples)
    unbatched = Sample.objects.filter(Q(site=object, batch=None, domain='mpi_eva'))
    if unbatched.exists() or not SampleBatch.objects.filter(site=object).exists():
        tmp, c = SampleBatch.objects.get_or_create(name="Undefined Batch", site=object)
        unbatched.update(batch=tmp)

    context = panel_context(request, object)
    context.update(filter_context(request, object))
    return render(request, "main/site/site-sample-content.html", context)


def get_site_batches(request, pk):
    """
    the sample batches of the DNA tab (with the sample-filters of the side-panel)
    """
    from main.tools.samplebatch import filter_samples

    object = Site.objects.get(pk=pk)
    samples = filter_samples(request, Sample.objects.filter(site=object))

    # Build base queryset
    sample_batch_ids = set(samples.order_by().values_list("batch_id", flat=True))
    batches_qs = SampleBatch.objects.filter(site=object).annotate(
        sample_count=Count('sample', filter=Q(sample__in=samples))
    )
    
    # for uploading, we need to have the option to add samples to an empty batch...
    # If user is not authenticated, only include batches linked to samples
    if not request.user.is_authenticated:
        batches_qs = batches_qs.filter(id__in=sample_batch_ids)

    batches_qs = batches_qs.order_by('name')

    # with sample-filters, only the batches with matching samples are shown
    filtered = any(request.session.get(key) for key in ["filter_layer_pk", "filter_culture", "filter_batch_pk", "filter_analyzed", "filter_no_layer"])

    # Final batch dictionary
    batch_sample_dict = {
        batch: batch.sample_count
        for batch in batches_qs
        if not (
            len(batches_qs) > 1
            and batch.name == "Undefined Batch"
            and batch.sample_count == 0
        )
        and not (filtered and batch.sample_count == 0)
    }

    context = {
        "batches": batch_sample_dict,
        "object": object,
        "filtered": filtered,
    }
    return render(request, "main/site/site-sample-batches.html", context)


## The human remains tab
def get_site_human_content(request, pk):
    site = Site.objects.get(pk=int(pk))

    if request.user.is_authenticated:
        remains = Sample.objects.filter(site=site, domain="archaeology").distinct().order_by('year_of_collection')
    else:
        remains = Sample.objects.filter(site=site, domain="archaeology", ref__isnull=False).distinct().order_by('year_of_collection')
    
    sample_references = Reference.objects.filter(sample__in=remains).distinct()

    context = {"object": site, "remains":remains, 'sample_references':sample_references}
    return render(request, "main/site/site-human-content.html", context)

### create sample-batch


@login_required
def samplebatch_create(request):
    if request.method == "POST":
        obj = SampleBatchForm(request.POST)
        obj.save()
        return get_site_sample_content(request)
    return get_site_sample_content(request)


## Samplebatch-TAB

# what the rows of the sample-table show, loaded in bulk instead of per row
# (the age: Sample.age_summary falls back to the parent sample, its dates and its layer)
SAMPLE_ROW_RELATED = [
    "batch", "date_upper", "date_lower",
    "sample__date_upper", "sample__date_lower", "sample__layer__date_upper", "sample__layer__date_lower",
    "layer__culture", "layer__layer", "layer__date_upper", "layer__date_lower",
]
SAMPLE_ROW_PREFETCH = ["project", "synonyms", "date", "sample__date", "layer__date", "sample__layer__date"]


def sample_synonym_types(samples_qs):
    """
    the synonym-types of the samples are the columns of the sample-table
    """
    return sorted(set(Synonym.objects.filter(sample__in=samples_qs).values_list("type", flat=True)), key=str)


def sample_row_context(request, sample):
    """
    the context to render a single row of the sample-table (sample-row.html), e.g. after editing the sample
    """
    combined = request.session.get("filter_combine")
    samples_qs = Sample.objects.filter(site=sample.site, domain='mpi_eva') if combined else Sample.objects.filter(batch=sample.batch)
    row = Sample.objects.filter(pk=sample.pk) \
        .select_related(*SAMPLE_ROW_RELATED) \
        .prefetch_related(*SAMPLE_ROW_PREFETCH) \
        .annotate(library_count=Count('analyzed_sample', filter=Q(analyzed_sample__project=get_project(request)))) \
        .first()
    return {
        "object": row,
        "request": request,
        "sample_synonyms": sample_synonym_types(samples_qs),
        # the batch-column is only shown in the combined table
        "batch": None if combined else sample.batch,
        "project": request.session.get("session_project"),
        "modal_url": reverse("main_modal_get"),
        "toggle_url": reverse("main_project_toggle"),
        "oob": True,
    }


def get_site_samplebatch_tab(request, pk):
    from main.tools.samplebatch import filter_samples
    # if pk=0, means we want to have all the batches from the site (that we are allowed to see)
    current_project = get_project(request)

    if pk != 0:
        batch = SampleBatch.objects.select_related('site').get(pk=pk)
        samples_qs = batch.sample.all()
        context = {"object": batch}
    else:
        site = get_instance_from_string(request.GET.get('object'))
        samples_qs = Sample.objects.filter(site=site, domain='mpi_eva').order_by('name')
        context = {
            'site': site,
            # all batches combined (Combine Batches in the filters of the DNA tab)
            "combined": True,
        }

    # the synonym-types of all samples are the columns of the sample-table
    context["sample_synonyms"] = sample_synonym_types(samples_qs)

    samples = samples_qs \
        .select_related(*SAMPLE_ROW_RELATED) \
        .prefetch_related(*SAMPLE_ROW_PREFETCH) \
        .annotate(library_count=Count('analyzed_sample', filter=Q(analyzed_sample__project=current_project)))
    samples = filter_samples(request, samples)
    if pk == 0:
        # all batches combined can be large: 300 samples per page (only the samples of the page are loaded)
        context["samples"] = Paginator(samples, 300).get_page(request.GET.get("page", 1))
        context["combined_url"] = reverse("main_samplebatch_get", args=[0]) + f"?object=site_{site.pk}"
    else:
        context["samples"] = list(samples)

    return render(request, "main/samples/sample-batch-tab.html", context)


## Add connections


@login_required
def update_connection(request):
    # check if a connection exists already
    try:
        connection = get_instance_from_string(request.POST.get("connection"))
    except:
        connection = Connection()

    # get the data from the form
    connection.name = request.POST.get("name")
    connection.link = request.POST.get("link")
    connection.short_description = request.POST.get("short_description")

    connection.save()
    connection.refresh_from_db()

    site = get_instance_from_string(request.POST.get("object"))
    site.connections.add(connection)

    request.GET._mutable = True
    request.GET.update(
        {
            "object": f"site_{site.pk}",
            "type": "connection_form",
            "fill": f"connection_{connection.pk}",
        }
    )

    from main.ajax import get_modal

    return get_modal(request)


def handle_stratigraphy(request, file):

    site = get_instance_from_string(request.POST.get("object"))

    def return_error(request, issues, df):
        return render(
            request,
            "main/modals/site_modal.html",
            {
                "object": get_instance_from_string(request.POST.get("object")),
                "type": "faunal_errors",
                "dataframe": df.fillna("").to_html(
                    index=False, classes="table table-striped col-12"
                ),
                "issues": issues,
            },
        )

    df = pd.read_csv(file, sep=",")
    df.drop_duplicates(inplace=True)
    # All required information is in the table

    ## 0. Verify the data-table
    from main.models import ProfileLayerJunction
    expected_columns = ProfileLayerJunction.table_columns()
    ## there can be more, but check that all required are in

    if not all(x in df.columns for x in expected_columns):
        missing = [x for x in expected_columns if x not in df.columns]
        issues = [f"Missing Table Columns: {x}" for x in missing]

        return return_error(request, issues, df)

    for n, (i, data) in enumerate(df.iterrows()):
        profile, _ = Profile.objects.get_or_create(site=site, name=data['Profile'].strip())
        layer, created = Layer.objects.get_or_create(site=site, name=data['Layer'].strip())

        #first, check if the parent of the layers exist or if they need to be created as well
        if data['Layer Parent'] == data['Layer Parent']:
            parent_layer, created = Layer.objects.get_or_create(site=site, name=data['Layer Parent'].strip())
            if not parent_layer == layer:
                layer.layer = parent_layer
                layer.save()

        # now get or create the ProfileLayerJunctions for the layer
        junction, _ = ProfileLayerJunction.objects.get_or_create(profile=profile, layer=layer)
        junction.position = n
        junction.save()
 

    return render(
        request,
        "main/modals/site_modal.html",
        {
            "object": get_instance_from_string(request.POST.get("object")),
            "type": "stratigraphy",
        },
    )


urlpatterns = [
    path("add-profile/<int:site_id>", add_profile, name="main_site_profile_create"),
    path("get-profile", get_site_profile_tab, name="main_profile-tab_get"),
    path("other-layers", get_site_other_layers, name="main_site_otherlayers"),
    path("create", site_create_update, name="main_site_add"),
    path("edit/<int:pk>", site_create_update, name="main_site_update"),
    path("list", SiteListView.as_view(), name="site_list"),
    path("<int:pk>", SiteDetailView.as_view(), name="site_detail"),
    path("element", get_site_element, name="main_site_element"),
    path("geodata", get_site_geo, name="main_site_geo"),
    path("sample-tab", get_site_sample_content, name="main_site_sample_tab"),
    path("<int:pk>/dna-batches", get_site_batches, name="main_site_batches"),
    path("<int:pk>/human-tab", get_site_human_content, name="main_site_human_get"),
    path("<int:site_id>/culture-css", get_culture_css, name="main_site_culture_css"),
    path("create-batch", samplebatch_create, name="main_samplebatch_create"),
    path(
        "get-samplebatch/<int:pk>",
        get_site_samplebatch_tab,
        name="main_samplebatch_get",
    ),
    path("connection-form", update_connection, name="main_site_addconnection"),
]
