from django.http import JsonResponse
from django.db.models import Q
from main.models import Layer, Profile, Site, Culture, models
from django.views.decorators.csrf import csrf_exempt

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

def add(request,pid):
    """
    add a new layer to an existing profile
    """
    profile = Profile.objects.get(pk=pid)
    try:
        layer = Layer.objects.get(pk=int(request.GET['layer']))
        layer.profile.add(profile)
        layer.site = profile.site
    except KeyError:
        layers = [x.pos for x in Layer.objects.filter(site__id=profile.site.pk).all()]
        last = max(layers) if len(layers)>0 else 0
        layer = Layer(name=f"Layer {last+1}", pos=last+1, site=profile.site)
        layer.save()
        layer.profile.add(profile)
    return JsonResponse({"pk":layer.pk, 'name':layer.name})

def remove_other(request,profile_id):
    """
    remove a layer from an existing profile (dont delete the layer itself)
    """
    profile = Profile.objects.get(pk=profile_id)
    layer = Layer.objects.get(pk=int(request.GET['layer']))
    layer.profile.remove(profile)
    return JsonResponse({"pk":layer.pk, 'name':layer.name})


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

def setname(request):
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