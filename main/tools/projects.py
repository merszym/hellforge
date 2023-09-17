from django.views.generic import ListView
from django.urls import path
from main.models import Project
from django.http import JsonResponse
from main.tools.generic import add_x_to_y_m2m, remove_x_from_y_m2m, get_instance_from_string, delete_x
from django.contrib.auth.decorators import login_required  # this is for now, make smarter later
from django.contrib.auth.mixins import LoginRequiredMixin  # this is for now, make smarter later
from django.shortcuts import redirect


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


class ProjectListView(ListView):
    model = Project
    template_name = "main/project/project_list.html"


urlpatterns = [
    path("list", ProjectListView.as_view(), name="main_project_list"),
    path("checkout/<str:namespace>", checkout_project, name="main_project_checkout"),
    path("close", close_project, name="main_project_close"),
]
