from django.views.generic import CreateView, ListView, UpdateView
from .models import Location

## Location Model
class LocationCreateView(CreateView):
    model = Location
    fields = ['name','geo']

class LocationListView(ListView):
    model = Location

class LocationDetailView(UpdateView):
    model = Location
    fields = ['name','geo']