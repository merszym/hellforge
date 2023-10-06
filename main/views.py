from django.views.generic import CreateView, ListView, UpdateView, DetailView, DeleteView
from django.urls import reverse
from django.shortcuts import render
from .models import (
    Location,
    Reference,
    Site,
    Layer,
    Culture,
    Date,
    Epoch,
    Checkpoint,
    DatingMethod,
    get_classname,
    Project,
)
from .forms import ReferenceForm, SiteForm, ProfileForm, CultureForm, DateForm, EpochForm, CheckpointForm, ContactForm
import json
import seaborn as sns
from django.db.models import Q
from collections import defaultdict
from main.tools.projects import get_project


# overwrite generic views to put project into context
class ProjectAwareListView(ListView):
    def get_context_data(self, **kwargs):
        context = super(ProjectAwareListView, self).get_context_data(**kwargs)
        context["project"] = get_project(self.request)
        return context

    def get_queryset(self, **kwargs):
        queryset = super(ProjectAwareListView, self).get_queryset(**kwargs)
        # 1. authenticated users are admin
        if self.request.user.is_authenticated:
            return queryset
        # 2. then project related view
        if project := get_project(self.request):
            try:
                return queryset.filter(project=project)  # catch lists that dont have a project
            except:
                pass
        # 3. #TODO return only completely public view
        return queryset


class ProjectAwareDetailView(DetailView):
    def get_context_data(self, **kwargs):
        context = super(ProjectAwareDetailView, self).get_context_data(**kwargs)
        context["project"] = get_project(self.request)
        return context


# now the other views..
def landing(request):
    return render(request, "main/common/landing.html")
