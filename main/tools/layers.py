from django.http import JsonResponse
from django.urls import path
from django.db.models import Q
from main.models import Layer, Profile, Site, Culture, models
from django.views.decorators.csrf import csrf_exempt
from main.tools.generic import add_x_to_y_m2m, get_instance_from_string
import copy

@csrf_exempt
def search(request):
    if kw := request.POST.get('keyword', False):
        q = Layer.objects.filter(Q(name__contains=kw) | Q(site__name__contains=kw ) )
        return JsonResponse({x.pk: f"{x.name};;{x.site}" for x in q})
    return JsonResponse({'status':False})

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
    pk = request.POST.get('pk')
    object = Layer.objects.get(pk=int(pk))
    object.name = request.POST.get('name')
    if unit := request.POST.get('unit', False):
        object.unit = unit
    else: object.unit = None
    object.save()
    return JsonResponse({'status':True})

def set_culture(request):
    if pk := request.POST.get('pk',False):
        if dat := request.POST.get('info', False):
            model,mpk = dat.split(',')
            model = models[model].objects.get(pk=int(mpk))
            model.culture = Culture.objects.get(pk=int(pk))
            model.save()
            return JsonResponse({"status":True})
    return JsonResponse({"status":False})

def remove_culture(request):
    if dat := request.POST.get('info', False):
        model,mpk = dat.split(',')
        model = models[model].objects.get(pk=int(mpk))
        model.culture = None
        model.save()
        return JsonResponse({"status":True})
    return JsonResponse({"status":False})

def set_parent(request):
    if pk := request.POST.get('pk',False):
        if parent := request.POST.get('parent', False):
            obj = Layer.objects.get(pk=int(pk))
            obj.parent = Layer.objects.get(pk=int(parent))
            obj.save()
            return JsonResponse({"status":True})
    return JsonResponse({"status":False})

def unset_parent(request):
    if info := request.POST.get('info',False):
        obj = Layer.objects.get(pk=int(info.split(',')[1]))
        obj.parent = None
        obj.save()
        return JsonResponse({"status":True})
    return JsonResponse({"status":False})

# and the respective urlpatterns
urlpatterns = [
    path('set-name',                 set_name,               name='main_layer_setname'),
    path('set-parent',               set_parent,             name='main_layer_setparent'),
    path('unset-parent',             unset_parent,           name='main_layer_unsetparent'),
    path('clone/<int:pk>',           clone,                  name='main_layer_clone'),
    path('search',                   search,                 name='main_layer_search'),
    path('positions/<int:site_id>',  update_positions,       name='main_layer_positionupdate'),
]