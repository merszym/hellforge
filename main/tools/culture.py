from django.views.generic import (
    CreateView,
    ListView,
    UpdateView,
    DetailView,
    DeleteView,
)
from django.urls import reverse
from django.http import JsonResponse
from django.shortcuts import render
from main.models import (
    Layer,
    Culture,
    Date,
    Epoch,
    DatingMethod,
    get_classname,
    Project,
    Description,
    Site,
)
from main.forms import CultureForm
from pathlib import Path
import json
import seaborn as sns
from django.db.models import Q
from collections import defaultdict
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)  # this is for now, make smarter later
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

        #  prepare the structures for the timeline
        nochildren = self.request.GET.get("nochildren", False)

        query = object.all_cultures(nochildren=nochildren)
        sites = Site.objects.filter(layer__culture__in=query)

        cult_color_dict = {
            cult: f"{col}"
            for cult, col in zip(query, sns.color_palette("husl", len(query)).as_hex())
        }

        items = []
        groupdata = []
        groupdata_tmp = {}

        for cult in query:
            cult_sites = (
                sites.filter(Q(layer__culture=cult))
                .distinct()
                .order_by("layer__culture__upper")
            )
            groupdata.append(
                {
                    "id": cult.pk,
                    "treeLevel": 2,
                    "content": (f"{cult.name}"),
                    "nestedGroups": [f"{cult.pk}-{site.pk}" for site in cult_sites],
                }
            )

            site_date_dict = {}
            for site in cult_sites:

                site_date_dict[site] = []

                groupdata_tmp[f"{cult.pk}-{site.pk}"] = {
                    "id": f"{cult.pk}-{site.pk}",
                    "content": f'{site.name}: <a href="{reverse("site_detail", kwargs={"pk":site.pk})}" class="btn-link">view</a>',
                    "treeLevel": 3,
                    # include the order within across sites within culture!
                }

            for layer in cult.layer.all():
                if len(layer.date.all()) == 0 and not layer.set_upper:
                    continue
                upper = layer.set_upper if layer.set_upper else layer.mean_upper
                lower = layer.set_lower if layer.set_lower else layer.mean_lower
                site_date_dict[layer.site].extend([int(lower), int(upper)])

            for site, v in site_date_dict.items():
                try:
                    maxv = max(v)
                    culturedata = {
                        "start": max(v) * -31556952
                        - (1970 * 31556952000),  # 1/1000 year in ms, start with year 0
                        "content": f"{site.name}",
                        "group": f"{cult.pk}-{site.pk}",
                        "type": "point",
                        "usesvg": False,
                        "method": f"{site.name}",
                        "oxa": "",
                    }
                    if max(v) != min(v):
                        culturedata.update(
                            {
                                "end": min(v) * -31556952 - (1970 * 31556952000),
                                "content": f"{max(v):,} - {min(v):,} years",
                                "style": f"background-color: {cult_color_dict[cult]};",
                                "type": "range",
                            }
                        )
                    items.append(culturedata)
                    # update the order of the groupdata
                    tmp = groupdata_tmp[f"{cult.pk}-{site.pk}"]
                    groupdata.append(tmp)

                except ValueError:  # no date for the site-culture
                    tmp = groupdata_tmp[f"{cult.pk}-{site.pk}"]
                    groupdata.append(tmp)
                    continue

        context["itemdata"] = json.dumps(items)
        context["groups"] = json.dumps(groupdata)
        return context


class CultureUpdateView(LoginRequiredMixin, UpdateView):
    model = Culture
    form_class = CultureForm
    extra_context = {"type": "Culture", "cultures": Culture.objects.all()}
    template_name = "main/culture/culture_form.html"

    def get_context_data(self, **kwargs):
        context = super(CultureUpdateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


class CultureCreateView(LoginRequiredMixin, CreateView):
    model = Culture
    form_class = CultureForm
    extra_context = {"type": "Culture", "cultures": Culture.objects.all()}

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
                    "nestedGroups": [
                        int(f"{n}{m}")
                        for m, subcult in enumerate(cult.all_cultures(noself=True))
                    ],
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


def get_culture_overview(request):
    object = Culture.objects.get(pk=int(request.GET.get("object")))
    return render(request, "main/culture/culture_overview.html", {"object": object})


def get_culture_geodata(request):
    # prepare the culture map
    object = Culture.objects.get(pk=int(request.GET.get("object")))
    nochildren = request.GET.get("nochildren", False)

    query = object.all_cultures(nochildren=nochildren)
    sites = Site.objects.filter(layer__culture__in=query)

    cult_color_dict = {
        cult: f"{col}"
        for cult, col in zip(query, sns.color_palette("husl", len(query)).as_hex())
    }

    geo = {"type": "FeatureCollection", "features": []}

    for cult in query:
        cult_sites = (
            sites.filter(Q(layer__culture=cult))
            .distinct()
            .order_by("layer__culture__upper")
        )
        for site in cult_sites:

            geo["features"].append(
                {
                    "type": "Feature",
                    "properties": {
                        "color": f"{cult_color_dict[cult]}",
                        "popupContent": f"<strong>{site.name}</strong><br><a href={reverse('site_detail', kwargs={'pk': site.id})} class=btn-link>Details</a>",
                    },
                    "geometry": site.geometry,
                }
            )

    return JsonResponse([geo], safe=False)


urlpatterns = [
    path("<int:pk>/edit", CultureUpdateView.as_view(), name="culture_update"),
    path("add", CultureCreateView.as_view(), name="culture_add"),
    path("list", CultureListView.as_view(), name="culture_list"),
    path("<int:pk>", CultureDetailView.as_view(), name="culture_detail"),
    path("overview", get_culture_overview, name="main_culture_overview"),
    path("geodata", get_culture_geodata, name="main_culture_geodata"),
]
