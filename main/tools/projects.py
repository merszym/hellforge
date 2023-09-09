from django.views.generic import ListView
from django.urls import path
from main.models import Project
from django.http import JsonResponse
from main.tools.generic import add_x_to_y_m2m, remove_x_from_y_m2m, get_instance_from_string, delete_x
from django.contrib.auth.decorators import login_required  # this is for now, make smarter later
from django.contrib.auth.mixins import LoginRequiredMixin  # this is for now, make smarter later


class ProjectListView(ListView):
    model = Project
    template_name = "main/project/project_list.html"


urlpatterns = [
    path("list", ProjectListView.as_view(), name="main_project_list"),
]
