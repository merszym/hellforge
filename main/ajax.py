from .forms import ReferenceForm, ProfileForm, DateForm
from django.http import JsonResponse
from django.shortcuts import render
from .models import Reference, Location, Site, Profile, Layer, Culture, Epoch, Checkpoint
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt


def save_date(request):
    form = DateForm(request.POST)
    if form.is_valid():
        obj = form.save()
        obj.refresh_from_db()
        return JsonResponse({"pk":obj.id, 'date':str(obj), 'upper':obj.upper, 'lower':obj.lower, 'method':obj.method})
    return JsonResponse({"pk":False})

def save_ref(request):
    form = ReferenceForm(request.POST)
    if form.is_valid():
        obj = form.save()
        obj.refresh_from_db()
        return JsonResponse({"pk":obj.id, 'title':obj.title, 'short':obj.short})
    return JsonResponse({"pk":False})

def save_profile(request,site_id):
    form = ProfileForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.site = Site.objects.get(pk=site_id)
        obj.save()
        return JsonResponse({"pk":obj.id, 'name':obj.name})
    return JsonResponse({"pk":False})

def get_profile(request, pk):
    profile = Profile.objects.get(pk=pk)
    return render(request,'main/profile/profile-detail.html', {'object':profile})

@csrf_exempt
def search_ref(request):
    data = {x:v[0] for (x,v) in dict(request.POST).items()}
    kw = data['keyword']
    q = Reference.objects.filter(Q(short__contains=kw) | Q(title__contains=kw ))
    return JsonResponse({x.pk:f"{x.short};;{x.title}" for x in q})

@csrf_exempt
def search_loc(request):
    data = {x:v[0] for (x,v) in dict(request.POST).items()}
    kw = data['keyword']
    q = Location.objects.filter(Q(name__contains=kw))
    return JsonResponse({x.pk:x.name for x in q})

@csrf_exempt
def search_culture(request):
    data = {x:v[0] for (x,v) in dict(request.POST).items()}
    kw = data['keyword']
    q = Culture.objects.filter(Q(name__contains=kw) | Q(description__contains=kw ))
    return JsonResponse({x.pk:x.name for x in q})

@csrf_exempt
def search_epoch(request):
    data = {x:v[0] for (x,v) in dict(request.POST).items()}
    kw = data['keyword']
    q = Epoch.objects.filter(Q(name__contains=kw) | Q(description__contains=kw ))
    return JsonResponse({x.pk:x.name for x in q})

@csrf_exempt
def search_cp(request):
    data = {x:v[0] for (x,v) in dict(request.POST).items()}
    kw = data['keyword']
    q = Checkpoint.objects.filter(Q(name__contains=kw) | Q(description__contains=kw ) | Q(category__contains=kw ) | Q(type__contains=kw ))
    return JsonResponse({x.pk: f"{x.name};;{x.type}" for x in q})

def save_layer(request,profile_id):
    """
    add a new layer to an existing profile
    """
    profile = Profile.objects.get(pk=profile_id)
    try:
        layer = Layer.objects.get(pk=int(request.GET['layer']))
        layer.profile.add(profile)
        layer.site = profile.site
    except KeyError:
        layers = [x.pos for x in Layer.objects.filter(profile__id=profile.pk).all()]
        layers.extend([x.pos for x in profile.other_layers])
        last = max(layers) if len(layers)>0 else 0
        layer = Layer(name=f"Layer {last+1}", pos=last+1, site=profile.site)
        layer.save()
        layer.profile.add(profile)
    return JsonResponse({"pk":layer.pk, 'name':layer.name})

def update_layer_positions(request, site_id):
    site = Site.objects.get(pk=site_id)
    #find the position that has changed
    new_positions = [int(x) for x in request.GET['new_positions'].split(',')]
    layers = [x for x in site.layers if x.pk in new_positions]
    for old,new in zip(layers,new_positions):
        pos = old.pos
        l = Layer.objects.get(pk=new)
        l.pos = pos
        l.save()
    return JsonResponse({'data':True})




