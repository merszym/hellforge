from django.views.generic import CreateView, ListView, UpdateView
from .models import Location, Reference
from .forms import LocationForm, ReferenceForm

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