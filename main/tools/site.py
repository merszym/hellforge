from django.urls import path
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
)
from copy import copy
import json
import seaborn as sns
from django.contrib.auth.mixins import LoginRequiredMixin  # this is for now, make smarter later
from django.contrib.auth.decorators import login_required  # this is for now, make smarter later
from collections import defaultdict
from django.shortcuts import get_object_or_404
from main.views import ProjectAwareListView, ProjectAwareDetailView
from main.tools.generic import add_x_to_y_m2m, remove_x_from_y_m2m


## Sites
class SiteDetailView(ProjectAwareDetailView):
    model = Site
    template_name = "main/site/site_detail.html"

    def get_context_data(self, **kwargs):
        context = super(SiteDetailView, self).get_context_data(**kwargs)
        tab = self.request.GET.get("tab", "layers")
        object = self.get_object()
        # get the first profile
        profile = object.profile.first()

        # get the project description
        try:
            project_description = Description.objects.get(project=context.get("project"), site=object)
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

        # load the samples and batches
        # first create a batch for the samples that dont have one yet...
        tmp, c = SampleBatch.objects.get_or_create(name="Undefined Batch", site=object)
        nobatch = Sample.objects.filter(Q(site=object, batch=None))
        for sample in nobatch:
            sample.batch = tmp
            sample.save()
        # then load the samples into a nested dict
        samples = nested_dict()
        sample_layers = nested_dict()

        # iterate over the batches
        for batch in object.sample_batch.all():
            # TODO: check if Undefined Batch should be displayed...
            if not "All" in samples[batch]:
                samples[batch]["All"] = []
            batch_samples = Sample.objects.filter(Q(site=object, batch=batch))
            # iterate over the layers
            for layer in sorted(list(set([x.layer for x in batch_samples])), key=lambda x: getattr(x, "pos", 0)):
                # get the samples
                qs = batch_samples.filter(layer=layer)
                if len(qs) > 0:
                    samples[batch]["All"].extend(qs)
                    if layer == None:
                        layer = "unknown"
                    samples[batch][layer] = qs
                    # add the layer to the layer-list
                    try:
                        sample_layers[batch].append(layer)
                    except:
                        sample_layers[batch] = ["All", layer]

        context.update(
            {
                "profile_form": ProfileForm,
                "samplebatch_form": SampleBatchForm,
                "tab": tab,
                "taxa": taxa,
                "taxa_references": set(taxrefs),
                "project_description": project_description,
                "profile": profile,
                "samples": samples,
                "sample_layers": sample_layers,
            }
        )
        return context


class SiteListView(ProjectAwareListView):
    model = Site
    template_name = "main/site/site_list.html"

    def get_queryset(self, **kwargs):
        queryset = super(SiteListView, self).get_queryset(**kwargs)
        return queryset.filter(child=None)


def get_timeline_data(site_id, hidden=False, related=False, curves=False):
    data = {}
    site = Site.objects.get(pk=site_id)
    layers = Layer.objects.filter(site=site).prefetch_related("date")
    cultures = {}
    for n, cult in enumerate(Culture.objects.filter(layer__in=layers).order_by("layer__pos")):
        cultures[cult.classname] = n

    groups = [
        {"id": layer.name.lower(), "content": layer.name, "treeLevel": 2, "order": int(layer.pos)} for layer in layers
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
        tmp_dates = list(layer.date.all())
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
                layerdata.update({"className": "hidden" if not (date.raw and curves) else "hiddenfill"})

            # if range instead of point
            if upper != lower:
                layerdata.update({"end": lower, "type": "range"})
            dates.append(layerdata)
    data["groups"] = json.dumps(groups)
    data["itemdata"] = json.dumps(dates)
    data["cultures"] = [
        (k, v)
        for k, v in zip(
            [x for x in sorted(cultures, key=lambda x: cultures[x])], sns.color_palette("husl", len(cultures)).as_hex()
        )
    ]
    return data


@login_required
def add_profile(request, site_id):
    """
    create and add a new profile within a Site
    """
    form = ProfileForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.site = Site.objects.get(pk=site_id)
        obj.save()
    return JsonResponse({"status": False})


# Sites ##
@login_required
def site_create_update(request, pk=None):
    object = Site.objects.get(pk=pk) if pk else None
    if request.method == "POST":
        form = SiteForm(request.POST, instance=copy(object))
        if form.is_valid():
            obj = form.save()
            description = Description(content_object=obj)
            description.save()
            if not obj.loc.first():
                loc = Location(geo=form.cleaned_data.get("geo"), name=f"{obj.name} Location")
                loc.save()
                loc.refresh_from_db()
                obj.loc.add(loc)
                return redirect(obj)
            else:
                loc = obj.loc.first()
                loc.geo = form.cleaned_data.get("geo")
                loc.save()
                return redirect(obj)
        return render(request, "main/site/site_form.html", {"object": object, "form": form})
    return render(request, "main/site/site_form.html", {"form": SiteForm(instance=copy(object)), "object": object})


urlpatterns = [
    path("add-profile/<int:site_id>", add_profile, name="main_site_profile_create"),
    path("create", site_create_update, name="main_site_add"),
    path("edit/<int:pk>", site_create_update, name="main_site_update"),
    path("list", SiteListView.as_view(), name="site_list"),
    path("<int:pk>", SiteDetailView.as_view(), name="site_detail"),
]
