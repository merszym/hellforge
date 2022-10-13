from django.views.generic import CreateView, ListView
from .models import Location

class LocationCreateView(CreateView):
    model = Location
    fields = ['name','geo']

class LocationListView(ListView):
    model = Location