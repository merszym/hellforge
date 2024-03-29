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
)
from copy import copy
import json
import seaborn as sns
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

        # create jsons for expected taxa:
        nested_dict = lambda: defaultdict(nested_dict)
        # Create an instance of the nested defaultdict
        taxa = nested_dict()
        taxrefs = []

        for layer in Layer.objects.filter(Q(site=object) & Q(assemblage__isnull=False)):
            # load the taxa
            for assemblage in layer.assemblage.all():
                for ref in assemblage.ref.all():
                    taxrefs.append(ref)
                for found_taxon in assemblage.taxa.all():
                    taxon = found_taxon.taxon
                    taxa[taxon.family][taxon][layer] = found_taxon.abundance

        context.update(
            {
                "taxa": taxa,
                "taxa_references": set(taxrefs),
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


def get_timeline_data(site_id, hidden=False, curves=False, request=False):
    if request:
        project = get_project(request)
    data = {}
    site = Site.objects.get(pk=site_id)
    layers = Layer.objects.filter(site=site).prefetch_related("date")
    cultures = {}
    for n, cult in enumerate(
        Culture.objects.filter(layer__in=layers).order_by("layer__pos")
    ):
        cultures[cult.classname] = n

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
        if sup := layer.set_upper:
            if slo := layer.set_lower:
                set_date = Date(upper=sup, lower=slo)
                # convert to ms
                sup, slo = set_date.to_ms()
                background = {
                    "start": sup,
                    "end": slo,
                    "order": sup * -1,
                    "content": f"{set_date}",
                    "group": layer.name.lower(),
                    "type": "background",
                    "background": True,
                }
                dates.append(background)

        # now for the dates
        if (project and site in project.site.all()) or (request.user.is_authenticated):
            tmp_dates = list(layer.date.all())
        else:
            # if not in project and view-only dont display unpublished dates
            tmp_dates = [x for x in list(layer.date.all()) if len(x.ref.all()) > 0]

        if hidden:
            tmp_dates.extend(layer.hidden_dates)
        for date in tmp_dates:
            upper, lower = date.to_ms()
            layerdata = {
                "start": upper,
                "order": upper * -1 if not date.hidden else upper * -4,
                "content": f"{date}",
                "group": layer.name.lower(),
                "className": layer.culture.classname if layer.culture else "sterile",
                "type": "point",
                "style": f"{'background-color: rgba(0,0,0,0); border: none;' if date.raw and curves else ''}",
                "usesvg": True if curves and date.raw else False,
                "polygon": f"{date.get_polygon_css() if date.raw else ''}",
                "oxa": f"{date.oxa if date.oxa else ''}",
                "method": date.method,
                "background": False,
            }
            if date.hidden:
                layerdata.update(
                    {
                        "className": (
                            "hidden" if not (date.raw and curves) else "hiddenfill"
                        )
                    }
                )

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
    data["cultures"] = [
        (k, v)
        for k, v in zip(
            [x for x in sorted(cultures, key=lambda x: cultures[x])],
            sns.color_palette("husl", len(cultures)).as_hex(),
        )
    ]
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
    return render(
        request, "main/site/site_elements.html", {"object": object, "element": element}
    )


def get_site_geo(request):
    locations = []
    if request.GET.get("all", False) == "1":
        for site in Site.objects.all():
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

    nested_dict = lambda: defaultdict(nested_dict)
    data = nested_dict()
    layers = nested_dict()

    # TODO: move to signals
    # Create a Gallery for each Batch
    if not batch.gallery:
        tmp = Gallery(title=batch.name)
        tmp.save()
        batch.gallery = tmp
        batch.save()

    batch_samples = Sample.objects.filter(batch=batch)

    # make a list of id-synonym keys that are necessary for the sample-table
    sample_synonyms = list(
        Synonym.objects.filter(sample__in=batch_samples)
        .values_list("type", flat=True)
        .distinct()
    )

    layers["All"] = 0
    for layer in sorted(
        list(set([x.layer for x in batch_samples])),
        key=lambda x: getattr(x, "pos", 0),
    ):
        # get the samples
        layer_samples = batch_samples.filter(layer=layer)

        layer_libraries = AnalyzedSample.objects.filter(sample__in=layer_samples)
        # and add them to the dict
        if len(layer_samples) > 0:
            if layer == None:
                layer = "unknown"
            # create All placeholders
            if not "All" in data["samples"]:
                data["samples"]["All"] = []
                data["libraries"]["All"] = []
            data["samples"]["All"].extend(layer_samples)
            data["libraries"]["All"].extend(layer_libraries)
            data["samples"][layer] = layer_samples
            data["libraries"][layer] = layer_libraries
            # add the layer to the layer-list

            layers[layer] = len(layer_samples)
            layers["All"] = layers["All"] + len(layer_samples)

    context = {
        "object": batch,
        "layers": layers,
        "data": data,
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
    path("create-batch", samplebatch_create, name="main_samplebatch_create"),
    path(
        "get-samplebatch/<int:pk>",
        get_site_samplebatch_tab,
        name="main_samplebatch_get",
    ),
    path("connection-form", update_connection, name="main_site_addconnection"),
]
