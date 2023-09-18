from django.views.generic import ListView, DetailView, UpdateView
from django.urls import path
from main.models import Project
from django.http import JsonResponse
from main.tools.generic import add_x_to_y_m2m, remove_x_from_y_m2m, get_instance_from_string, delete_x
from django.contrib.auth.decorators import login_required  # this is for now, make smarter later
from django.contrib.auth.mixins import LoginRequiredMixin  # this is for now, make smarter later
from django.shortcuts import redirect, render


def get_project(request):
    if namespace := request.session.get("session_project", False):
        return Project.objects.get(namespace=namespace)
    return None


def checkout_project(request, namespace):
    # Store the selected project in the session.
    # only set the cookie if project exists
    try:
        Project.objects.get(namespace=namespace)
        request.session["session_project"] = namespace
    except:
        pass
    return redirect("landing")


def close_project(request):
    del request.session["session_project"]
    return redirect("landing")


def get_project_status_tile(request):
    return render(request, "main/project/project_status_tile.html", {"project": get_project(request)})


class ProjectListView(ListView):
    model = Project
    template_name = "main/project/project_list.html"


class ProjectUpdateView(UpdateView):
    model = Project
    fields = "__all__"
    template_name = "main/project/project_update.html"


class ProjectDetailView(DetailView):
    model = Project
    template_name = "main/project/project_detail.html"
    slug_url_kwarg = "namespace"
    slug_field = "namespace"


urlpatterns = [
    path("list", ProjectListView.as_view(), name="main_project_list"),
    path("checkout/<str:namespace>", checkout_project, name="main_project_checkout"),
    path("close", close_project, name="main_project_close"),
    path("status", get_project_status_tile, name="main_project_status"),
    path("<str:namespace>", ProjectDetailView.as_view(), name="main_project_detail"),
    path("<int:pk>/edit", ProjectUpdateView.as_view(), name="main_project_update"),
]
