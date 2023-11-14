from django.views.generic import ListView, DetailView
from django.shortcuts import render
from .models import Project
from main.tools.projects import get_project


# overwrite generic views to put project into context
class ProjectAwareListView(ListView):
    def get_context_data(self, **kwargs):
        context = super(ProjectAwareListView, self).get_context_data(**kwargs)
        project = get_project(self.request)
        context["project"] = project
        context["project_sites"] = project.site.all() if project else []
        return context


class ProjectAwareDetailView(DetailView):
    def get_context_data(self, **kwargs):
        context = super(ProjectAwareDetailView, self).get_context_data(**kwargs)
        project = get_project(self.request)
        context["project"] = project
        context["project_sites"] = project.site.all() if project else []
        return context


# now the other views..
def landing(request):
    return render(request, "main/common/landing.html")
