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
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)  # this is for now, make smarter later
from django.urls import path


## Epoch ##
class EpochUpdateView(LoginRequiredMixin, UpdateView):
    model = Epoch
    template_name = "main/epoch/epoch_form.html"
    form_class = EpochForm


class EpochCreateView(LoginRequiredMixin, CreateView):
    model = Epoch
    form_class = EpochForm
    template_name = "main/epoch/epoch_form.html"


urlpatterns = [
    path("<int:pk>/edit", EpochUpdateView.as_view(), name="epoch_update"),
    path("add", EpochCreateView.as_view(), name="epoch_add"),
]
