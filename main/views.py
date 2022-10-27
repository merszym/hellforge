from django.views.generic import CreateView, ListView, UpdateView, DetailView, DeleteView
from django.urls import reverse
from .models import Location, Reference, Site, Layer, Culture, Date, Epoch, Checkpoint, Profile
from .forms import LocationForm, ReferenceForm, SiteForm, ProfileForm, LayerForm, CultureForm, DateForm, DateUpdateForm, EpochForm, CheckpointForm
import re
import statistics


## Locations ##
class LocationCreateView(CreateView):
    model = Location
    form_class = LocationForm
    extra_context = {'reference_form': ReferenceForm}

    def get_context_data(self, **kwargs):
        context = super(LocationCreateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


class LocationListView(ListView):
    model = Location


class LocationUpdateView(UpdateView):
    model = Location
    form_class = LocationForm
    extra_context = {'reference_form': ReferenceForm}

    def get_context_data(self, **kwargs):
        context = super(LocationUpdateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


## References ##
class ReferenceCreateView(CreateView):
    model = Reference
    fields = "__all__"


class ReferenceListView(ListView):
    model = Reference


class ReferenceUpdateView(UpdateView):
    model = Reference
    fields = "__all__"


## Sites ##
class SiteCreateView(CreateView):
    model = Site
    form_class = SiteForm
    extra_context = {'reference_form': ReferenceForm}

    def get_context_data(self, **kwargs):
        context = super(SiteCreateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


class SiteListView(ListView):
    model = Site


class SiteUpdateView(UpdateView):
    model = Site
    form_class = SiteForm
    extra_context = {'reference_form': ReferenceForm}

    def get_context_data(self, **kwargs):
        context = super(SiteUpdateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


class SiteDetailView(DetailView):
    model = Site
    extra_context = {'profile_form': ProfileForm}

    def get_context_data(self, **kwargs):
        context = super(SiteDetailView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

## Profiles ##

class ProfileDeleteView(DeleteView):
    model = Profile
    template_name = 'main/confirm_delete.html'

    def get_success_url(self):
        return reverse('site_detail', kwargs={'pk':self.get_object().site.id})


## Layers ##
class LayerUpdateView(UpdateView):
    model = Layer
    form_class = LayerForm
    extra_context = {'reference_form': ReferenceForm, 'dating_form': DateForm}

    def get_context_data(self, **kwargs):
        context = super(LayerUpdateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

class LayerDeleteView(DeleteView):
    model = Layer
    template_name = 'main/confirm_delete.html'

    def get_success_url(self):
        if self.get_object().site:
            return reverse('site_detail', kwargs={'pk':self.get_object().site.id})
        else:
            return reverse('site_detail', kwargs={'pk':self.get_object().profile.first().site.id})


## Cultures ##
class CultureUpdateView(UpdateView):
    model = Culture
    form_class = CultureForm
    extra_context = {'reference_form': ReferenceForm, 'dating_form': DateForm, 'type':'Culture'}

    def get_context_data(self, **kwargs):
        context = super(CultureUpdateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


class CultureCreateView(CreateView):
    model = Culture
    fields = CultureForm
    extra_context = {'reference_form': ReferenceForm, 'dating_form': DateForm,  'type':'Culture'}

    def get_context_data(self, **kwargs):
        context = super(CultureCreateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


class CultureListView(ListView):
    model = Culture


## Dates ##
class DateUpdateView(UpdateView):
    model = Date
    form_class = DateUpdateForm
    extra_context = {'reference_form': ReferenceForm}

    def get_context_data(self, **kwargs):
        context = super(DateUpdateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


## Epoch ##
class EpochUpdateView(UpdateView):
    model = Epoch
    template_name = 'main/culture_form.html'
    form_class = EpochForm
    extra_context = {'reference_form': ReferenceForm, 'dating_form': DateForm, 'type':'Epoch'}

    def get_context_data(self, **kwargs):
        context = super(EpochUpdateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


class EpochCreateView(CreateView):
    model = Epoch
    form_class = EpochForm
    template_name = 'main/culture_form.html'
    extra_context = {'reference_form': ReferenceForm, 'dating_form': DateForm, 'type':'Epoch'}

    def get_context_data(self, **kwargs):
        context = super(EpochCreateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


class EpochListView(ListView):
    model = Epoch
    template_name = 'main/culture_list.html'
    extra_context = {'type': 'Epoch'}

    def get_context_data(self, **kwargs):
        context = super(EpochListView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


## Checkpoints
class CheckpointCreateView(CreateView):
    model = Checkpoint
    form_class = CheckpointForm
    extra_context = {'reference_form': ReferenceForm, 'dating_form': DateForm,}

    def get_context_data(self, **kwargs):
        context = super(CheckpointCreateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


class CheckpointUpdateView(UpdateView):
    model = Checkpoint
    form_class = CheckpointForm
    extra_context = {'reference_form': ReferenceForm, 'dating_form': DateForm,}

    def get_context_data(self, **kwargs):
        context = super(CheckpointUpdateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context