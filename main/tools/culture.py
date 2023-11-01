from django.views.generic import CreateView, ListView, UpdateView, DetailView, DeleteView
from django.urls import reverse
from django.shortcuts import render
from main.models import Layer, Culture, Date, Epoch, DatingMethod, get_classname, Project, Description
from main.forms import (
    ReferenceForm,
    CultureForm,
    DateForm,
)
from pathlib import Path
import json
import seaborn as sns
from django.db.models import Q
from collections import defaultdict
from django.contrib.auth.mixins import LoginRequiredMixin  # this is for now, make smarter later
from django.urls import path
from main.views import ProjectAwareDetailView, ProjectAwareListView


## Cultures ##
class CultureDetailView(ProjectAwareDetailView):
    model = Culture
    template_name = "main/culture/culture_detail.html"

    # create the nested groups for the timeline template
    def get_context_data(self, **kwargs):
        object = self.object
        # the lacy check if a description is missing...
        if not object.description.first():
            tmp = Description(content_object=object)
            tmp.save()

        context = super(CultureDetailView, self).get_context_data(**kwargs)
        items = []
        groupdata = []
        groupdata_tmp = {}
        geo = {"type": "FeatureCollection", "features": []}
        nochildren = self.request.GET.get("nochildren", False)
        query = sorted(self.object.all_cultures(nochildren=nochildren), key=lambda x: x.upper * -1)
        # get the colors right
        ordered_sites = sorted(
            self.object.all_sites(nochildren=nochildren),
            key=lambda x: (x[0].upper, x[1].lowest_date(cult=self.object, nochildren=nochildren)),
        )
        all_sites = []
        [all_sites.append(site.name) for (cult, site) in ordered_sites if site.name not in all_sites]

        site_color_dict = {
            site.lower(): f"{col}" for site, col in zip(all_sites, sns.color_palette("husl", len(all_sites)).as_hex())
        }
        for cult in sorted(query, key=lambda x: int(x.upper)):
            ordered_sites = sorted(cult.all_sites(nochildren=True), key=lambda x: x[1].lowest_date(cult=cult) * -1)
            sites = []
            [sites.append(site) for (cult, site) in ordered_sites if site not in sites]
            if len(sites) == 0:
                continue
            groupdata.append(
                {
                    "id": cult.name.lower(),
                    "treeLevel": 2,
                    "content": f"{cult.name} | {cult.upper} - {cult.lower} ya",
                    "order": int(cult.upper),
                    "nestedGroups": [f"{cult.name.lower()}-{site.name.lower()}" for site in sites],
                }
            )
            site_date_dict = {}
            for site in sites:
                site_date_dict[site.name] = []
                geo["features"].append(
                    {
                        "type": "Feature",
                        "properties": {
                            "color": f"{site_color_dict[site.name.lower()]}",
                            "popupContent": f"<strong>{site.name}</strong><br><a href={reverse('site_detail', kwargs={'pk': site.id})} class=btn-link>Details</a>",
                        },
                        "geometry": site.geometry,
                    }
                )
                groupdata_tmp[f"{cult.name.lower()}-{site.name.lower()}"] = {
                    "id": f"{cult.name.lower()}-{site.name.lower()}",
                    "content": f'{site.name}: <a href="{reverse("site_detail", kwargs={"pk":site.pk})}" class="btn-link">view</a>',
                    "treeLevel": 3,
                    # include the order within across sites within culture!
                }

            for layer in cult.layer.all():
                if len(layer.date.all()) == 0 and not layer.set_upper:
                    continue
                upper = layer.set_upper if layer.set_upper else layer.mean_upper
                lower = layer.set_lower if layer.set_lower else layer.mean_lower
                site_date_dict[layer.site.name].extend([int(lower), int(upper)])

            for k, v in site_date_dict.items():
                try:
                    maxv = max(v)
                    culturedata = {
                        "start": max(v) * -31556952 - (1970 * 31556952000),  # 1/1000 year in ms, start with year 0
                        "content": f"{k} | {max(v):,} ya",
                        "group": f"{cult.name.lower()}-{k.lower()}",
                        "type": "point",
                        "usesvg": False,
                        "method": "Site",
                    }
                    if max(v) != min(v):
                        culturedata.update(
                            {
                                "end": min(v) * -31556952 - (1970 * 31556952000),
                                "content": f"{k} | {max(v):,} - {min(v):,} ya",
                                "style": f"background-color: {site_color_dict[k.lower()]};",
                                "type": "range",
                            }
                        )
                    items.append(culturedata)
                    # update the order of the groupdata
                    tmp = groupdata_tmp[f"{cult.name.lower()}-{k.lower()}"]
                    tmp["order"] = max(v)
                    groupdata.append(tmp)

                except ValueError:  # no date for the site-culture
                    tmp = groupdata_tmp[f"{cult.name.lower()}-{k.lower()}"]
                    groupdata.append(tmp)
                    continue

        context["itemdata"] = json.dumps(items)
        context["groups"] = json.dumps(groupdata)
        context["geo"] = geo
        return context


class CultureUpdateView(LoginRequiredMixin, UpdateView):
    model = Culture
    form_class = CultureForm
    extra_context = {
        "reference_form": ReferenceForm,
        "dating_form": DateForm,
        "type": "Culture",
        "datingoptions": DatingMethod.objects.all(),
    }
    template_name = "main/culture/culture_form.html"

    def get_context_data(self, **kwargs):
        context = super(CultureUpdateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


class CultureCreateView(LoginRequiredMixin, CreateView):
    model = Culture
    form_class = CultureForm
    extra_context = {
        "reference_form": ReferenceForm,
        "dating_form": DateForm,
        "type": "Culture",
        "datingoptions": DatingMethod.objects.all(),
    }
    template_name = "main/culture/culture_form.html"

    def get_context_data(self, **kwargs):
        context = super(CultureCreateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


class CultureListView(ProjectAwareListView):
    model = Culture
    template_name = "main/culture/culture_list.html"

    def get_context_data(self, **kwargs):
        context = super(CultureListView, self).get_context_data(**kwargs)
        items = []
        groupdata = []

        query = Culture.objects.filter(culture__isnull=True)

        for n, cult in enumerate(query):
            groupdata.append(
                {
                    "id": cult.name.lower(),
                    "content": f"<a class='btn-link' href={reverse('culture_detail', kwargs={'pk':cult.pk})}>{cult.name}</a> | {cult.upper} - {cult.lower} ya",
                    "treeLevel": 2,
                    "nestedGroups": [int(f"{n}{m}") for m, subcult in enumerate(cult.all_cultures(noself=True))],
                }
            )
            for m, subcult in enumerate(cult.all_cultures(noself=True)):
                groupdata.append(
                    {
                        "id": int(f"{n}{m}"),
                        "content": f"{subcult} <a class='btn-link' href={reverse('culture_detail', kwargs={'pk':subcult.pk})}>view</a>",
                        "order": int(f"{n}{m}"),
                        "treeLevel": 3,
                    }
                )
                items.append(
                    {
                        "start": int(subcult.upper) * -31556952
                        - (1970 * 31556952000),  # 1/1000 year in ms, start with year 0
                        "end": int(subcult.lower) * -31556952 - (1970 * 31556952000),
                        "content": f"{subcult} | {subcult.upper} - {subcult.lower}",
                        "group": int(f"{n}{m}"),
                    }
                )
        context["itemdata"] = items
        context["timelinedata"] = groupdata
        return context


urlpatterns = [
    path("<int:pk>/edit", CultureUpdateView.as_view(), name="culture_update"),
    path("add", CultureCreateView.as_view(), name="culture_add"),
    path("list", CultureListView.as_view(), name="culture_list"),
    path("<int:pk>", CultureDetailView.as_view(), name="culture_detail"),
]
