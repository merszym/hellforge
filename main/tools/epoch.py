from django.views.generic import CreateView, ListView, UpdateView
from main.models import (
    Reference,
    Culture,
    Date,
    Epoch,
    DatingMethod,
)
from main.forms import (
    ReferenceForm,
    EpochForm,
    DateForm,
)
from pathlib import Path
import json
from django.db.models import Q
from collections import defaultdict
from django.contrib.auth.decorators import login_required  # this is for now, make smarter later
from django.contrib.auth.mixins import LoginRequiredMixin  # this is for now, make smarter later
from django.urls import path


## Epoch ##
class EpochUpdateView(LoginRequiredMixin, UpdateView):
    model = Epoch
    template_name = "main/culture/culture_form.html"
    form_class = EpochForm
    extra_context = {
        "reference_form": ReferenceForm,
        "dating_form": DateForm,
        "type": "Epoch",
        "datingoptions": DatingMethod.objects.all(),
    }

    def get_context_data(self, **kwargs):
        context = super(EpochUpdateView, self).get_context_data(**kwargs)
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


class EpochCreateView(LoginRequiredMixin, CreateView):
    model = Epoch
    form_class = EpochForm
    template_name = "main/culture/culture_form.html"
    extra_context = {
        "reference_form": ReferenceForm,
        "dating_form": DateForm,
        "type": "Epoch",
        "datingoptions": DatingMethod.objects.all(),
    }

    def get_context_data(self, **kwargs):
        context = super(EpochCreateView, self).get_context_data(**kwargs)
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


class EpochListView(LoginRequiredMixin, ListView):
    model = Epoch
    template_name = "main/culture/culture_list.html"
    extra_context = {"type": "Epoch"}

    def get_context_data(self, **kwargs):
        context = super(EpochListView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


urlpatterns = [
    path("<int:pk>/edit", EpochUpdateView.as_view(), name="epoch_update"),
    path("add", EpochCreateView.as_view(), name="epoch_add"),
    path("list", EpochListView.as_view(), name="epoch_list"),
]
