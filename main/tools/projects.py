from django.views.generic import ListView, DetailView, UpdateView
from django.urls import path
from main.models import Project, Description, Site, Sample
from django.http import JsonResponse
from main.tools.generic import add_x_to_y_m2m, remove_x_from_y_m2m, get_instance_from_string, delete_x, download_csv
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin  # this is for now, make smarter later
import hashlib
from collections import defaultdict
import pandas as pd
import json


def get_project(request):
    if namespace := request.session.get("session_project", False):
        return Project.objects.get(namespace=namespace)
    return None


def checkout_project(request, namespace):
    # Store the selected project in the session.
    # only set the cookie if project exists
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
                    pass  # TODO: display wrong password message
        else:
            request.session["session_project"] = namespace
    except:
        pass
    return redirect(tmp)


def close_project(request):
    del request.session["session_project"]
    return redirect("landing")


def get_project_status_tile(request):
    return render(request, "main/project/project_status_tile.html", {"project": get_project(request)})


def get_dataset(request):
    if project := get_project(request):
        qs = Sample.objects.filter(project=project).order_by("layer__site", "layer__name")
        # TODO: make this some sort of API!
        q = []
        for s in qs:
            q.append(
                {
                    "Project": project.name,
                    "Site": s.site.name,
                    "Site Id": s.site.coredb_id,
                    "Layer": s.layer.name if s.layer else "Unassigned",
                    "Culture": s.layer.culture.name if (s.layer and s.layer.culture) else None,
                    "Umbrella Culture": s.layer.culture.get_highest().name if (s.layer and s.layer.culture) else None,
                    "Epoch": s.layer.epoch.name if (s.layer and s.layer.epoch) else None,
                    "Layer Age": s.layer.age_summary(export=True) if s.layer else None,
                    "Sample Type": s.type,
                    "Sample Name": s.name,
                    "Sample Synonyms": ";".join([str(x) for x in s.synonyms.all()]),
                    "Year of Collection": s.year_of_collection,
                    "Sample Provenience": ";".join([f"{k}:{v}" for k, v in json.loads(s.provenience).items()]),
                }
            )
        df = pd.DataFrame.from_records(q)
        return download_csv(df, name=f"samples_{project.namespace}.csv")

    return redirect("landing")


class ProjectListView(ListView):
    model = Project
    template_name = "main/project/project_list.html"

    def get_context_data(self, **kwargs):
        context = super(ProjectListView, self).get_context_data(**kwargs)
        queryset = self.get_queryset()
        public_project = queryset.filter(published=True)
        private_projects = queryset.filter(published=False)

        context.update({"public_projects": public_project, "private_projects": private_projects})
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
        if project.password:
            context["public_link_pw"] = hashlib.md5(project.password.encode()).hexdigest()
        if not project.project_description.first():
            tmp = Description(content_object=project)
            tmp.save()
        # display the project sites
        object_list = sorted(Site.objects.filter(project=project, child=None), key=lambda x: x.country)
        context["object_list"] = object_list
        # get the related samples
        sample_dict = defaultdict(int)
        for site in object_list:
            sample_dict[site.name] = Sample.objects.filter(project=project, site=site)
        context["sample_list"] = Sample.objects.filter(project=project)
        context["sample_dict"] = sample_dict
        return context


urlpatterns = [
    path("list", ProjectListView.as_view(), name="main_project_list"),
    path("checkout/<str:namespace>", checkout_project, name="main_project_checkout"),
    path("close", close_project, name="main_project_close"),
    path("status", get_project_status_tile, name="main_project_status"),
    path("get-dataset", get_dataset, name="main_project_get_dataset"),
    path("<str:namespace>", ProjectDetailView.as_view(), name="main_project_detail"),
    path("<int:pk>/edit", ProjectUpdateView.as_view(), name="main_project_update"),
]
