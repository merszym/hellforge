from django.views.generic import CreateView, ListView, UpdateView, DetailView
from .models import Location, Reference, Site, Layer, Culture, Date, Epoch
from .forms import LocationForm, ReferenceForm, SiteForm, ProfileForm, LayerForm, CultureForm, DateForm, DateUpdateForm, EpochForm

## Locations ##

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

## Layers ##

class LayerUpdateView(UpdateView):
    model = Layer
    form_class = LayerForm
    extra_context = {'reference_form': ReferenceForm}

    def get_context_data(self, **kwargs):
        context = super(LayerUpdateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

    def form_valid(self, form):
        self.object = form.save()
        refs = [int(x) for x in form.cleaned_data.get('reflist').split(',') if x != '']
        for pk in refs:
            self.object.ref.add(Reference.objects.get(pk=pk))
        self.object.save()
        return super().form_valid(form)

## Cultures ##

class CultureUpdateView(UpdateView):
    model = Culture
    form_class = CultureForm
    extra_context = {'reference_form': ReferenceForm, 'dating_form': DateForm, 'type':'Culture'}

    def get_context_data(self, **kwargs):
        context = super(CultureUpdateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

    def form_valid(self, form):
        self.object = form.save()
        refs = [int(x) for x in form.cleaned_data.get('reflist').split(',') if x != '']
        locs = [int(x) for x in form.cleaned_data.get('loclist').split(',') if x != '']
        dates = [int(x) for x in form.cleaned_data.get('datelist').split(',') if x != '']
        for pk in refs:
            self.object.ref.add(Reference.objects.get(pk=pk))
        if len(locs) != 0:
            self.object.loc.clear()
            for pk in locs:
                self.object.loc.add(Location.objects.get(pk=pk))
        print(dates)
        for pk in dates:
            self.object.date.add(Date.objects.get(pk=pk))
        self.object.save()
        return super().form_valid(form)


class CultureCreateView(CreateView):
    model = Culture
    form_class = CultureForm
    extra_context = {'reference_form': ReferenceForm, 'dating_form': DateForm,  'type':'Culture'}

    def get_context_data(self, **kwargs):
        context = super(CultureCreateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

    def form_valid(self, form):
        self.object = form.save()
        self.object.loc.clear()
        refs = [int(x) for x in form.cleaned_data.get('reflist').split(',') if x != '']
        locs = [int(x) for x in form.cleaned_data.get('loclist').split(',') if x != '']
        dates = [int(x) for x in form.cleaned_data.get('datelist').split(',') if x != '']
        for pk in refs:
            self.object.ref.add(Reference.objects.get(pk=pk))
        for pk in locs:
            self.object.loc.add(Location.objects.get(pk=pk))
        for pk in dates:
            self.object.date.add(Date.objects.get(pk=pk))
        self.object.save()
        return super().form_valid(form)

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

    def form_valid(self, form):
        self.object = form.save()
        refs = [int(x) for x in form.cleaned_data.get('reflist').split(',') if x != '']
        for pk in refs:
            self.object.ref.add(Reference.objects.get(pk=pk))
        self.object.save()
        return super().form_valid(form)

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

    def form_valid(self, form):
        self.object = form.save()
        refs = [int(x) for x in form.cleaned_data.get('reflist').split(',') if x != '']
        locs = [int(x) for x in form.cleaned_data.get('loclist').split(',') if x != '']
        dates = [int(x) for x in form.cleaned_data.get('datelist').split(',') if x != '']
        for pk in refs:
            self.object.ref.add(Reference.objects.get(pk=pk))
        if len(locs) != 0:
            self.object.loc.clear()
            for pk in locs:
                self.object.loc.add(Location.objects.get(pk=pk))
        for pk in dates:
            self.object.date.add(Date.objects.get(pk=pk))
        self.object.save()
        return super().form_valid(form)


class EpochCreateView(CreateView):
    model = Epoch
    form_class = EpochForm
    template_name = 'main/culture_form.html'

    extra_context = {'reference_form': ReferenceForm, 'dating_form': DateForm, 'type':'Epoch'}

    def get_context_data(self, **kwargs):
        context = super(EpochCreateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

    def form_valid(self, form):
        self.object = form.save()
        self.object.loc.clear()
        refs = [int(x) for x in form.cleaned_data.get('reflist').split(',') if x != '']
        locs = [int(x) for x in form.cleaned_data.get('loclist').split(',') if x != '']
        dates = [int(x) for x in form.cleaned_data.get('datelist').split(',') if x != '']
        for pk in refs:
            self.object.ref.add(Reference.objects.get(pk=pk))
        for pk in locs:
            self.object.loc.add(Location.objects.get(pk=pk))
        for pk in dates:
            self.object.date.add(Date.objects.get(pk=pk))
        self.object.save()
        return super().form_valid(form)

class EpochListView(ListView):
    model = Epoch
    template_name = 'main/culture_list.html'
    extra_context = {'type': 'Epoch'}

    def get_context_data(self, **kwargs):
        context = super(EpochListView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context