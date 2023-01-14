from django.urls import path
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import CreateView, ListView, UpdateView, DetailView
from main.forms import ProfileForm, SiteForm, ReferenceForm, ContactForm, DateForm
from main.models import Site, DatingMethod, Location, Culture, Checkpoint, Layer
from copy import copy
import json
import seaborn as sns

def get_timeline_data(site_id):
    data = {}
    site = Site.objects.get(pk=site_id)
    layers = Layer.objects.filter(site=site).prefetch_related('date')
    cultures = {}
    for n,cult in enumerate(Culture.objects.filter(layer__in=layers).order_by('layer__pos')):
        cultures[cult.classname] = n
    groups = [
        {
        "id":layer.name.lower(),
        "content":layer.name,
        'treeLevel':2,
        "order": int(layer.pos)
        }
        for layer in layers
    ]
    dates = []
    for layer in layers:
        for date in layer.date.all():
            upper, lower = date.to_ms()
            layerdata = {
                "start": upper,
                "order": upper*-1,
                "content": f"{date}",
                "group": layer.name.lower(),
                "className":f"{layer.culture.classname if layer.culture else 'sterile'}",
                "type":"point"
            }
            # if range instead of point
            if (upper != lower):
                layerdata.update({
                    "end": lower,
                    "type": "range"
                })
            dates.append(layerdata)
    data['groups'] = json.dumps(groups)
    data['itemdata'] = json.dumps(dates)
    data['cultures'] = [
        (k,v) for k,v in zip(
            [x for x in sorted(cultures, key=lambda x: cultures[x])],
            sns.color_palette('husl',len(cultures)).as_hex()
        )
    ]
    return data

def add_profile(request, site_id):
    """
    create and add a new profile within a Site
    """
    form = ProfileForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.site = Site.objects.get(pk=site_id)
        obj.save()
        return render(request, 'main/site/profile_list.html', {'object':obj.site})
    return JsonResponse({"status":False})

# Sites ##
def site_create_update(request, pk=None):
    object = Site.objects.get(pk=pk) if pk else None
    if request.method == 'POST':
        form = SiteForm(request.POST, instance=copy(object))
        if form.is_valid():
            obj = form.save()
            if not obj.loc.first():
                loc = Location(geo=form.cleaned_data.get('geo'), name=f"{obj.name} Location")
                loc.save()
                loc.refresh_from_db()
                obj.loc.add(loc)
                return redirect(obj)
            else:
                loc = obj.loc.first()
                loc.geo = form.cleaned_data.get('geo')
                loc.save()
                return redirect(obj)
        return render(request, 'main/site/site_form.html', {'object': object, 'form':form})
    return render(request, 'main/site/site_form.html', {'form':SiteForm(instance=copy(object)), 'object':object})

class SiteDescriptionUpdateView(DetailView):
    model = Site
    template_name = 'main/site/site_description_update.html'
    extra_context = {'readonly': False}

    def get_context_data(self, **kwargs):
        context = super(SiteDescriptionUpdateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

urlpatterns = [
    path('add-profile/<int:site_id>', add_profile,                         name='main_site_profile_create'),
    path('create',                    site_create_update,                  name='main_site_add'),
    path('edit/<int:pk>',             site_create_update,                  name='main_site_update'),
    path('edit/desc/<int:pk>',        SiteDescriptionUpdateView.as_view(), name='main_site_descr_update'),
]