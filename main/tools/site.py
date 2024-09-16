from django.urls import path, reverse
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import CreateView, ListView, UpdateView, DetailView
from django.db.models import Q
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
            Q(layer__in=layers) | Q(layer_analysis__site__layer__in=layers)
        ).order_by("layer__pos")
    ):
        cultures[cult.classname] = n

    context["cultures"] = [
        (k, v)
        for k, v in zip(
            [x for x in sorted(cultures, key=lambda x: cultures[x])],
            sns.color_palette("husl", len(cultures)).as_hex(),
        )
    ]
    return render(request, "main/site/site_culture_css.html", context)


def get_timeline_data(site_id, request=False, profile=None):
    if request:
        project = get_project(request)
    data = {}
    site = Site.objects.get(pk=site_id)

    if profile:
        layers = Layer.objects.filter(
            Q(site=site) & Q(profile=profile)
        ).prefetch_related("date")
    else:
        layers = Layer.objects.filter(Q(site=site)).prefetch_related("date")

    groups = [
        {
            "id": layer.name.lower(),
            "content": layer.name,
            "treeLevel": 2,
            "order": int(layer.pos),
        }
        for layer in layers
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
                content.append(f"(sample {date.sample_model.first().name})")
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

    context = {
        "object": object,
        "selected_profile": selected_profile,
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
    try:
        object = get_instance_from_string(request.GET.get("object"))
    except TypeError:  # object is in POST not GET
        object = Site.objects.get(pk=int(request.POST.get("object")))
    context = {"object": object}
    # load the samples and batches
    # first create a batch for the samples that dont have one yet...
    tmp, c = SampleBatch.objects.get_or_create(name="Undefined Batch", site=object)
    nobatch = Sample.objects.filter(Q(site=object, batch=None))
    for sample in nobatch:
        sample.batch = tmp
        sample.save()
    # The get the number of samples per batch for display in the site-sample-tab

    batches = list(SampleBatch.objects.filter(site=object))
    batch_samples = defaultdict(int)

    for batch in batches:
        # hide Undefinied batch if empty and other ones exist
        if (
            (len(batches) > 1)
            and (batch.name == "Undefined Batch")
            and (len(batch.sample.all()) == 0)
        ):
            continue
        # create All placeholders
        batch_samples[batch] = len(batch.sample.all())

    # check if a batch is selected already
    if selected_batch := request.GET.get("samplebatch", False):
        selected_batch = get_instance_from_string(selected_batch)
    else:
        selected_batch = batches[0]

    context.update(
        {
            "sample": object.sample.first(),
            "batches": batch_samples,
            "selected_batch": selected_batch,
        }
    )
    return render(request, "main/site/site-sample-content.html", context)


## DNA content
def get_site_dna_content(request, pk):
    site = Site.objects.get(pk=int(pk))
    context = {"object": site}

    # first, get the objects
    query = QuicksandAnalysis.objects.filter(
        Q(analyzedsample__sample__site=site) & Q(analyzedsample__qc_pass=True)
    ).order_by("analyzedsample")

    if request.method == "POST":
        if prset := request.POST.get("probe", False):
            if prset != "all":
                if prset == "AA163":  # get all the human mt probesets
                    query = query.filter(analyzedsample__probes__in=["AA163", "AA22"])
                else:
                    query = query.filter(analyzedsample__probes=prset)
                context.update({"probe": prset})

        mode = request.POST.get("mode", "absolute")
        column = request.POST.get("column", "ReadsDeduped")
        percentage = float(request.POST.get("percentage", 0.5))
        breadth = float(request.POST.get("breadth", 0.5))
        ancient = "on" == request.POST.get("ancient", "")
        positives = "on" == request.POST.get("positives", "")
        only_project = "on" == request.POST.get("only_project", "")

        # column: ReadsDeduped
        # mode: relative,absolute
        # filter: ancient, breadth, percentage

        context.update(
            prepare_data(
                request,
                query,
                column=column,
                percentage=percentage,
                breadth=breadth,
                mode=mode,
                ancient=ancient,
                positives=positives,
                only_project=only_project,
            )
        )
    else:
        context.update(prepare_data(request, query))

    return render(request, "main/site/site-dna-content.html", context)


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
    batch = SampleBatch.objects.get(pk=pk)

    # get the defaults for display
    current_project = get_project(request)

    # TODO: move to signals
    # Create a Gallery for each Batch
    if not batch.gallery:
        tmp = Gallery(title=batch.name)
        tmp.save()
        batch.gallery = tmp
        batch.save()

    batch_samples = Sample.objects.filter(batch=batch).distinct()

    # include the negative controls
    control_batches = set(
        batch_samples.exclude(negative_control_batch__isnull=True).values_list(
            "negative_control_batch", flat=True
        )
    )
    batch_samples = Sample.objects.filter(
        Q(batch=batch) | (Q(negative_control_batch__in=control_batches) & Q(type="ENC"))
    ).distinct()

    # now filter the samples
    layer = request.POST.get("layer", "all")
    profile = request.POST.get("profile", "all")
    analyzed = "on" == request.POST.get("analyzed", "")
    all_projects = "on" == request.POST.get("all_projects", "")

    if layer != "all":
        layer = get_instance_from_string(layer)
        batch_samples = batch_samples.filter(layer=layer)

    if profile != "all":
        profile = get_instance_from_string(profile)
        batch_samples = batch_samples.filter(layer__profile=profile)

    if analyzed:
        batch_samples = batch_samples.filter(analyzed_sample__isnull=False)

    if not all_projects and current_project:
        batch_samples = batch_samples.filter(project=current_project)

    # make a list of id-synonym keys that are necessary for the sample-table
    sample_synonyms = list(
        Synonym.objects.filter(sample__in=batch_samples)
        .values_list("type", flat=True)
        .distinct()
    )

    layers = Layer.objects.filter(sample__batch=batch).distinct()

    if profile != "all":
        layers = layers.filter(profile=profile)

    profiles = Profile.objects.filter(layer__sample__batch=batch).distinct()

    analyzedsamples = AnalyzedSample.objects.filter(sample__in=batch_samples)

    context = {
        "object": batch,
        "layers": layers,
        "profiles": profiles,
        "sample_synonyms": sample_synonyms,
        "samples": batch_samples,
        "analyzedsamples": analyzedsamples,
        "all_projects": all_projects,
        "analyzed": analyzed,
        "layer": layer,
        "profile": profile,
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
    expected_columns = ["Layer Name", "Layer Culture", "Layer Epoch"]
    ## there can be more, but check that all required are in

    if not all(x in df.columns for x in expected_columns):
        missing = [x for x in expected_columns if x not in df.columns]
        issues = [f"Missing Table Columns: {x}" for x in missing]

        return return_error(request, issues, df)

    for n, (i, data) in enumerate(df.iterrows()):
        try:
            layer = Layer.objects.get(site=site, name=data["Layer Name"].strip())
            layer.pos = n
            layer.save()

        except Layer.DoesNotExist:
            return return_error(
                request,
                [f'Layer: {data["Layer Name"]} doesnt exist'],
                pd.DataFrame(
                    {k: v for k, v in zip(data.index, data.values)}, index=[0]
                ),
            )

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
    path("get-profile", get_site_profile_tab, name="main_profile_get"),
    path("create", site_create_update, name="main_site_add"),
    path("edit/<int:pk>", site_create_update, name="main_site_update"),
    path("list", SiteListView.as_view(), name="site_list"),
    path("<int:pk>", SiteDetailView.as_view(), name="site_detail"),
    path("element", get_site_element, name="main_site_element"),
    path("geodata", get_site_geo, name="main_site_geo"),
    path("sample-tab", get_site_sample_content, name="main_site_sample_tab"),
    path("<int:pk>/dna-tab", get_site_dna_content, name="main_site_dna_tab"),
    path("<int:site_id>/culture-css", get_culture_css, name="main_site_culture_css"),
    path("create-batch", samplebatch_create, name="main_samplebatch_create"),
    path(
        "get-samplebatch/<int:pk>",
        get_site_samplebatch_tab,
        name="main_samplebatch_get",
    ),
    path("connection-form", update_connection, name="main_site_addconnection"),
]
