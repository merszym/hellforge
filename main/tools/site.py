from django.urls import path
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import CreateView, ListView, UpdateView, DetailView
from django.db.models import Q
from main.forms import ProfileForm, SiteForm, ReferenceForm, ContactForm, DateForm
from main.models import Site, DatingMethod, Location, Culture, Checkpoint, Layer, Date, Description, Project
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
        # load the samples
        samples = nested_dict()

        for layer in Layer.objects.filter(Q(site=object)):
            qs = layer.sample.filter(project=context.get("project"))
            if len(qs) > 0:
                if not "All" in samples:
                    samples["All"] = []
                samples["All"].extend(qs)
                samples[layer] = qs

        context.update(
            {
                "profile_form": ProfileForm,
                "tab": tab,
                "taxa": taxa,
                "taxa_references": set(taxrefs),
                "project_description": project_description,
                "profile": profile,
                "samples": samples,
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
