from django.views.generic import ListView, DetailView, UpdateView
from django.urls import path, reverse
from django.db.models import Q
from main.models import Project, Description, Site, Sample, AnalyzedSample
from main.tools.analyzed_samples import update_query_for_negatives
from django.http import JsonResponse, HttpResponse
from main.tools.generic import (
    add_x_to_y_m2m,
    remove_x_from_y_m2m,
    get_instance_from_string,
    delete_x,
    download_csv,
)
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)  # this is for now, make smarter later
import hashlib
from collections import defaultdict
import pandas as pd
import json
from django.contrib.auth.decorators import (
    login_required,
)


def get_project(request):
    if namespace := request.session.get("session_project", False):
        return Project.objects.get(namespace=namespace)
    return None


def checkout_project(request, namespace):
    # Store the selected project in the session.
    # only set the cookie if project exists
    tmp = None
    try:
        tmp = Project.objects.get(namespace=namespace)
        if (tmp.password != "") and (request.user.is_authenticated == False):
            # check the link hash
            expected = hashlib.md5(tmp.password.encode()).hexdigest()
            if given := request.GET.get("pw", False):
                # verify
                if given == expected:
                    request.session["session_project"] = namespace
                else:
                    # dont set cookie, return to project list
                    return redirect("main_project_list")
        else:
            request.session["session_project"] = namespace
        # jump to a specific site
        if goto_site := request.GET.get("goto_site", False):
            site = Site.objects.get(pk=int(goto_site))
            return redirect(site)
    except:
        return redirect("main_project_list")
    return redirect(tmp)


def close_project(request):
    if "session_project" in request.session:
        del request.session["session_project"]
    return redirect("main_project_list")


def get_project_status_tile(request):
    return render(
        request,
        "main/project/project_status_tile.html",
        {"project": get_project(request)},
    )


class ProjectListView(ListView):
    model = Project
    template_name = "main/project/project_list.html"

    def get_context_data(self, **kwargs):
        context = super(ProjectListView, self).get_context_data(**kwargs)
        queryset = self.get_queryset()
        public_project = queryset.filter(published=True)
        private_projects = queryset.filter(published=False)

        context.update(
            {"public_projects": public_project, "private_projects": private_projects}
        )
        return context


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    fields = ["name", "password"]
    template_name = "main/project/project_update.html"


class ProjectDetailView(DetailView):
    model = Project
    template_name = "main/project/project_detail.html"
    slug_url_kwarg = "namespace"
    slug_field = "namespace"

    def get_context_data(self, **kwargs):
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        # this is quick and dirty - create a description if non exists for a project
        project = self.get_object()

        # this is only because I am too lazy to make it into a signal
        if not project.project_description.first():
            tmp = Description(content_object=project)
            tmp.save()

        # display the project sites
        object_list = sorted(
            Site.objects.filter(project=project, child=None), key=lambda x: x.country
        )
        context["object_list"] = object_list

        sample_dict = defaultdict(int) # for the number of collected samples
        analyzedsample_dict = defaultdict() 

        for site in object_list:
            qs = Sample.objects.filter(
                    Q(site=site) & Q(project=project)
                )
            sample_dict[site.name] = len(qs)

            analyzedsample_dict[site.name] = defaultdict()
            
            libs = AnalyzedSample.objects.filter(
                Q(sample__site=site) &
                Q(sample__project=project) &
                Q(project=project)
            )

            analyzedsample_dict[site.name]["libraries"] = len(libs)
            analyzedsample_dict[site.name]["controls"] = len(update_query_for_negatives(libs).filter(sample__isnull=True))
            analyzedsample_dict[site.name]["samples"] = len(set(libs.values_list("sample", flat=True)))
        
        # summary stats
        context["sample_dict"] = sample_dict
        context["analyzedsample_dict"] = analyzedsample_dict
        return context


def get_project_geo(request):
    object = Project.objects.get(pk=int(request.GET.get("object")))
    locations = []
    for site in object.site.all():
        try:
            geo = json.loads(site.loc.first().geo)
        except TypeError:
            # apparently some objects are not saved as json, but as dict???
            geo = site.loc.first().geo
        except AttributeError:  # no location found
            pass
        if geo:
            site_view_url = reverse("site_detail", kwargs={"pk": site.pk})
            geo["features"][0]["properties"][
                "popupContent"
            ] = f"<strong>{site.name}</strong><br><a href={site_view_url} class=btn-link>Details</a>"
            geo["features"][0]["properties"]["id"] = f"{site.pk}"
            locations.append(geo)
    return JsonResponse(locations, safe=False)


def get_project_overview(request):
    object = Project.objects.get(pk=int(request.GET.get("object")))
    context = {"object": object}
    # get context data
    sites = Site.objects.filter(project=object, child=None).values("pk")
    site_count = len(sites)
    sample_count = len(Sample.objects.filter(project=object, site__pk__in=sites).values("pk"))
    
    # get the related libraries
    qs = AnalyzedSample.objects.filter(
            Q(sample__site__project=object)
            & Q(sample__project=object)
            & Q(project=object)
        )
    qs = update_query_for_negatives(qs)
    
    analyzedsample_count = len(
        set(
            qs.exclude(sample__isnull=True).values_list(
                "sample", flat=True
            )
        )
    )
    library_count = len(qs.exclude(sample__isnull=True).values("pk"))
    negatives_count = len(qs.filter(sample__isnull=True).values("pk"))

    context["site_count"] = site_count
    context["sample_count"] = sample_count
    context["analyzedsample_count"] = analyzedsample_count
    context["library_count"] = library_count
    context["negatives_count"] = negatives_count
    context["total"] = len(qs)

    object_list = sorted(
        Site.objects.filter(project=object, child=None), key=lambda x: x.country
    )
    context["object_list"] = object_list

    return render(request, "main/project/project_overview.html", context)


def toggle_project(request):
    project = get_project(request)
    instance = get_instance_from_string(request.POST.get("instance_x"))

    request.POST._mutable = True
    request.POST.update({"instance_y": f"project_{project.pk}"})

    if project in instance.project.all():  # needs to get removed
        removed, instance, project = remove_x_from_y_m2m(request, response=False)
        # return the 'No' html
        return HttpResponse("<span style='color:red; cursor:pointer;'>No</span>")
    else:
        added, instance, project = add_x_to_y_m2m(request, response=False)
        # return the 'Yes' html
        return HttpResponse("<span style='color:green; cursor:pointer;'>Yes</span>")


urlpatterns = [
    path("list", ProjectListView.as_view(), name="main_project_list"),
    path("checkout/<str:namespace>", checkout_project, name="main_project_checkout"),
    path("close", close_project, name="main_project_close"),
    path("status", get_project_status_tile, name="main_project_status"),
    path("overview", get_project_overview, name="main_project_overview"),
    path("geodata", get_project_geo, name="main_project_geo"),
    path("toggle", toggle_project, name="main_project_toggle"),
    path("<str:namespace>", ProjectDetailView.as_view(), name="main_project_detail"),
    path("<int:pk>/edit", ProjectUpdateView.as_view(), name="main_project_update"),
]
