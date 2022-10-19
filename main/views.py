from django.views.generic import CreateView, ListView, UpdateView, DetailView
from .models import Location, Reference, Site
from .forms import LocationForm, ReferenceForm, SiteForm, ProfileForm

## Location Model
class LocationCreateView(CreateView):
    model = Location
    form_class = LocationForm
    extra_context = {'reference_form': ReferenceForm}

    def get_context_data(self, **kwargs):
        context = super(LocationCreateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

    def form_valid(self, form):
        self.object = form.save()
        refs = [int(x) for x in form.cleaned_data.get('reflist').split(',') if x != '']
        for pk in refs:
            self.object.ref.add(Reference.objects.get(pk=pk))
        self.object.save()
        return super().form_valid(form)

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

    def form_valid(self, form):
        self.object = form.save()
        refs = [int(x) for x in form.cleaned_data.get('reflist').split(',') if x != '']
        for pk in refs:
            self.object.ref.add(Reference.objects.get(pk=pk))
        self.object.save()
        return super().form_valid(form)

class ReferenceCreateView(CreateView):
    model = Reference
    fields = "__all__"

class ReferenceListView(ListView):
    model = Reference

class ReferenceUpdateView(UpdateView):
    model = Reference
    fields = "__all__"

class SiteCreateView(CreateView):
    model = Site
    form_class = SiteForm
    extra_context = {'reference_form': ReferenceForm}

    def get_context_data(self, **kwargs):
        context = super(SiteCreateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

    def form_valid(self, form):
        self.object = form.save()
        refs = [int(x) for x in form.cleaned_data.get('reflist').split(',') if x != '']
        locs = [int(x) for x in form.cleaned_data.get('loclist').split(',') if x != '']
        for pk in refs:
            self.object.ref.add(Reference.objects.get(pk=pk))
        for pk in locs:
            self.object.loc.add(Location.objects.get(pk=pk))
        self.object.save()
        return super().form_valid(form)

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

    def form_valid(self, form):
        self.object = form.save()
        self.object.loc.clear()
        refs = [int(x) for x in form.cleaned_data.get('reflist').split(',') if x != '']
        locs = [int(x) for x in form.cleaned_data.get('loclist').split(',') if x != '']
        for pk in refs:
            self.object.ref.add(Reference.objects.get(pk=pk))
        for pk in locs:
            self.object.loc.add(Location.objects.get(pk=pk))
        self.object.save()
        return super().form_valid(form)

class SiteDetailView(DetailView):
    model = Site
    extra_context = {'profile_form': ProfileForm}

    def get_context_data(self, **kwargs):
        context = super(SiteDetailView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context