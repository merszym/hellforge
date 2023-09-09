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
from django.contrib.auth.decorators import login_required  # this is for now, make smarter later
from django.contrib.auth.mixins import LoginRequiredMixin  # this is for now, make smarter later


@login_required
def landing(request):
    return render(request, "main/common/landing.html")


## Checkpoints
class CheckpointCreateView(CreateView):
    model = Checkpoint
    form_class = CheckpointForm
    extra_context = {
        "reference_form": ReferenceForm,
        "dating_form": DateForm,
        "datingoptions": DatingMethod.objects.all(),
    }

    def get_context_data(self, **kwargs):
        context = super(CheckpointCreateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save()
        date = Date(upper=form.cleaned_data.get("upper"), lower=form.cleaned_data.get("lower"), method="hidden")
        date.save()
        date.refresh_from_db()
        self.object.date.add(date)
        return super().form_valid(form)


class CheckpointUpdateView(UpdateView):
    model = Checkpoint
    form_class = CheckpointForm
    extra_context = {
        "reference_form": ReferenceForm,
        "dating_form": DateForm,
        "datingoptions": DatingMethod.objects.all(),
    }

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save()
        date = Date(upper=form.cleaned_data.get("upper"), lower=form.cleaned_data.get("lower"), method="hidden")
        date.save()
        date.refresh_from_db()
        self.object.date.add(date)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(CheckpointUpdateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context
