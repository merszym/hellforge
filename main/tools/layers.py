from django.http import JsonResponse
from django.urls import path, reverse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DeleteView, UpdateView
from main.models import Layer, Profile, Site, Culture, models
from main.forms import LayerForm, ReferenceForm
from main.tools.generic import add_x_to_y_m2m, get_instance_from_string, set_x_fk_to_y
import copy

def clone(request, pk):
    new_layer = Layer.objects.get(pk=pk)
    layer = Layer.objects.get(pk=pk)
    new_layer.pk = None
    # find the last postion:
    layers = [x.pos for x in Layer.objects.filter(site__id=Layer.objects.get(pk=pk).site.pk).all()]
    new_layer.pos = max(layers)+1
    new_layer.save()
    for profile in layer.profile.all():
        new_layer.profile.add(profile)
    for ref in layer.ref.all():
        new_layer.ref.add(ref)
    for cp in layer.checkpoint.all():
        new_layer.checkpoint.add(cp)
    return JsonResponse({'pk':new_layer.pk})

def update_positions(request, site_id):
    site = Site.objects.get(pk=site_id)
    #find the position that has changed
    new_positions = [int(x) for x in request.GET['new_positions'].split(',')]
    layers = [x for x in site.layer.all() if x.pk in new_positions]
    for old,new in zip(layers,new_positions):
        pos = old.pos
        l = Layer.objects.get(pk=new)
        l.pos = pos
        l.save()
    return JsonResponse({'data':True})

def set_name(request):
    object = get_instance_from_string(request.POST.get('info'))
    object.name = request.POST.get('name')
    object.unit = request.POST.get('unit', None)
    object.save()
    return JsonResponse({'status':True})

class LayerDeleteView(DeleteView):
    model = Layer
    template_name = 'main/confirm_delete.html'

    def get_success_url(self):
        if self.get_object().site:
            return reverse('site_detail', kwargs={'pk':self.get_object().site.id})
        else:
            return reverse('site_detail', kwargs={'pk':self.get_object().profile.first().site.id})

# TODO: this is mostly deprectated, finish the replacement and remove!
class LayerUpdateView(UpdateView):
    model = Layer
    form_class = LayerForm
    extra_context = {'reference_form': ReferenceForm}
    template_name = 'main/layer/layer_form.html'

    def get_context_data(self, **kwargs):
        context = super(LayerUpdateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


# and the respective urlpatterns
urlpatterns = [
    path('set-name',                 set_name,                  name='main_layer_setname'),
    path('clone/<int:pk>',           clone,                     name='main_layer_clone'),
    path('positions/<int:site_id>',  update_positions,          name='main_layer_positionupdate'),
    path('delete/<int:pk>',          LayerDeleteView.as_view(), name='main_layer_delete'),
    path('edit/<int:pk>',            LayerUpdateView.as_view(), name='main_layer_update'),
]