from django.urls import path, reverse
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import CreateView, ListView, UpdateView, DetailView
from django.db.models import Q, Count
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
    layers = Layer.objects.filter(Q(site=site))

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
    if request:
        project = get_project(request)
    data = {}
    site = Site.objects.get(pk=site_id)

    if profile:
        layers = Layer.objects.filter(
            Q(site=site) & Q(profile_junction__profile=profile)
        ).prefetch_related("date")
    else:
        layers = Layer.objects.filter(Q(site=site)).prefetch_related("date")

    unique_groups = set(layers)
    groups = [
        {
            "id": layer.name.lower(),
            "content": layer.name,
            "treeLevel": 2,
            "order": ProfileLayerJunction.objects.filter(layer=layer, profile=profile).first().position,
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
        if (project and site in project.site.all()) or (request.user.is_authenticated):
            tmp_dates = list(layer.date.all())
        else:
            # if not in project and view-only dont display unpublished dates
            tmp_dates = [x for x in list(layer.date.all()) if len(x.ref.all()) > 0]

        # now add the dates from the samples that are NOT also in the layers
        sample_dates = Date.objects.filter(
            Q(sample_model__in=layer.sample.all()) & Q(layer_model__isnull=True)
        )

        if not (project and site in project.site.all()) or not (
            request.user.is_authenticated
        ):
            sample_dates = sample_dates.filter(ref__isnull=False)

        tmp_dates.extend(list(sample_dates))

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

    # get the project context
    project = get_project(request)
        
    context = {
        "object": object,
        "selected_profile": selected_profile,
        "project_sites": list(project.site.values_list('pk', flat=True)) if project else []
    }

    return render(request, "main/site/site-profile-content.html", context)


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
    from main.tools.samplebatch import filter_samples, unset_sample_filters
    from main.tools.analyzed_samples import unset_library_filters

    # unset the library- and sample-level filters
    # because if we reload the page or go to a different site, we dont want prefiltered data

    unset_library_filters(request)
    unset_sample_filters(request)

    if request.method == 'POST':
        """This means we set filters for the downstream views!"""       
        # now filter the samples
        layer = request.POST.get("layer", "all")
        culture = request.POST.get("culture", "all")
        analyzed = "on" == request.POST.get("analyzed", "")
        combine = "on" == request.POST.get("combine", "")

        if layer != "all":
            layer = get_instance_from_string(layer)
            request.session['filter_layer_pk'] = layer.pk
            request.session['filter_layer_name'] = layer.name
        
        if culture != "all":
            culture = get_instance_from_string(culture)
            request.session['filter_culture_pk'] = culture.pk
            request.session['filter_culture_name'] = culture.name

        request.session['filter_analyzed'] = True if analyzed else False
        request.session['filter_combine'] = True if combine else False
        
        try:
            object = Site.objects.get(pk=int(request.POST.get("object")))
        except:
            object = get_instance_from_string(request.POST.get('object'))
            
    else:
        object = get_instance_from_string(request.GET.get("object"))

    # load the samples and batches
    # first create a batch for the samples that dont have one yet...
    tmp, c = SampleBatch.objects.get_or_create(name="Undefined Batch", site=object)
    Sample.objects.filter(Q(site=object, batch=None, domain='mpi_eva')).update(batch=tmp)
    
    # first, get all the samples that we need
    samples_qs = Sample.objects.filter(site=object) \
        .select_related(
            'site',
            'sample',
            'sample__layer',
            'sample__layer__layer',
            'sample__layer__layer__layer',
            'layer',
            'layer__layer',
            'layer__layer__layer',
            'layer__culture',
            'batch'
    ).prefetch_related('analyzed_sample','project')

    samples = filter_samples(request, samples_qs)

    # Build base queryset
    sample_batch_ids = {sample.batch_id for sample in samples if sample.batch_id}
    batches_qs = SampleBatch.objects.filter(site=object).annotate(
        sample_count=Count('sample', filter=Q(sample__in=samples))
    )
    
    # for uploading, we need to have the option to add samples to an empty batch...
    # If user is not authenticated, only include batches linked to samples
    if not request.user.is_authenticated:
        batches_qs = batches_qs.filter(id__in=sample_batch_ids)

    batches_qs = batches_qs.order_by('name')

    # Final batch dictionary
    batch_sample_dict = {
        batch: batch.sample_count
        for batch in batches_qs
        if not (
            len(batches_qs) > 1
            and batch.name == "Undefined Batch"
            and batch.sample_count == 0
        )
    }

    layers = Layer.objects.filter(
        Q(site=object, sample__isnull=False)
        | Q(site=object, child__sample__isnull=False)
        | Q(site=object, child__child__sample__isnull=False) # this should work in some other way...
        ).distinct()

    probes = {
        analyzed.probes
        for sample in samples_qs
        for analyzed in sample.analyzed_sample.all()
        if analyzed.probes is not None
    }

    context={
        "sample": samples.first(),
        "batches": batch_sample_dict,
        'layers': layers,
        'cultures': Culture.objects.filter(layer__in=layers).distinct(),
        'probes': probes,
        'object':object
        }

    return render(request, "main/site/site-sample-content.html", context)


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

def get_site_samplebatch_tab(request, pk):
    from main.tools.samplebatch import filter_samples
    # if pk=0, means we want to have all the batches from the site (that we are allowed to see)
    current_project = get_project(request)

    if pk != 0:
        batch = SampleBatch.objects \
            .select_related(
                'site',
            ) \
            .prefetch_related(
                'sample',
                'sample__synonyms',
                'sample__sample',
                'sample__layer',
                'sample__layer__culture',
                'sample__analyzed_sample',
            ) \
            .get(pk=pk)

        # get the defaults for display
        batch_samples = batch.sample.annotate(
            library_count=Count('analyzed_sample', filter=Q(analyzed_sample__project=current_project))
        ).all()

        # make a list of id-synonym keys that are necessary for the sample-table
        sample_synonyms = {
            synonym.type
            for sample in batch_samples
            for synonym in sample.synonyms.all()
        }

        context = {
            "object": batch,
            "sample_synonyms": sample_synonyms,
            "samples": filter_samples(request, batch_samples)
        }
    
    else:
        site = get_instance_from_string(request.GET.get('object'))
        samples_qs = Sample.objects.filter(site=site, domain='mpi_eva') \
            .select_related(
                'site',
                'sample',
                'sample__layer',
                'layer',
                'layer__culture',
                'batch'
            ).prefetch_related(
                'analyzed_sample',
                'synonyms'
            ) \
            .annotate(library_count=Count('analyzed_sample', filter=Q(analyzed_sample__project=current_project))) \
            .order_by('name')

        sample_synonyms = {
            synonym.type
            for sample in samples_qs
            for synonym in sample.synonyms.all()
        }

        context={
            'samples' : filter_samples(request, samples_qs),
            'site':site,
            "sample_synonyms": sample_synonyms,
        }

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
    path("create", site_create_update, name="main_site_add"),
    path("edit/<int:pk>", site_create_update, name="main_site_update"),
    path("list", SiteListView.as_view(), name="site_list"),
    path("<int:pk>", SiteDetailView.as_view(), name="site_detail"),
    path("element", get_site_element, name="main_site_element"),
    path("geodata", get_site_geo, name="main_site_geo"),
    path("sample-tab", get_site_sample_content, name="main_site_sample_tab"),
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
