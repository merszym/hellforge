from .forms import ReferenceForm, ProfileForm, DateForm, ContactForm
from django.http import JsonResponse
from django.shortcuts import render
from .models import Reference, Location, Site, Profile, Layer, Culture, Epoch, Checkpoint, ContactPerson, Image, Gallery
from django.db.models import Q
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import json

models = {
    'site': Site
}

@csrf_exempt
def upload_image(request):
    data = {k:v[0] for k,v in dict(request.GET).items()}
    model = models[data['model']]
    object = model.objects.get(pk=data['id'])

    if object.gallery:
        gallery = object.gallery
    else:
        gallery = Gallery(title=f"{str(object)}: Gallery")
        gallery.save()
        object.gallery = gallery
        object.save()

    img = dict(request.FILES)['image'][0]
    image = Image(image=img, gallery=gallery)
    image.save()
    image.refresh_from_db()

    if image.pk:
        success = 1
        url = image.image.url
    else:
        success = 0
        url = ''

    res = {
    "success" : success,
    "file": {
        "url" : url,
        }
    }
    return JsonResponse(res)

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

def save_contact(request):
    form = ContactForm(request.POST)
    if form.is_valid():
        obj = form.save()
        obj.refresh_from_db()
        return JsonResponse({"pk":obj.id, 'name':obj.name})
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
    q = Reference.objects.filter(Q(short__contains=kw) | Q(title__contains=kw ) | Q(tags__contains=kw ))
    return JsonResponse({x.pk:f"{x.short};;{x.title}" for x in q})

@csrf_exempt
def search_contact(request):
    data = {x:v[0] for (x,v) in dict(request.POST).items()}
    kw = data['keyword']
    q = ContactPerson.objects.filter(Q(name__contains=kw) | Q(email__contains=kw ) | Q(affiliation__contains=kw ))
    return JsonResponse({x.pk:f"{x.name}" for x in q})

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

@csrf_exempt
def search_layer(request):
    data = {x:v[0] for (x,v) in dict(request.POST).items()}
    kw = data['keyword']
    q = Layer.objects.filter(Q(name__contains=kw) | Q(site__name__contains=kw ) )
    print(q)
    return JsonResponse({x.pk: f"{x.name};;{x.site}" for x in q})

def clone_layer(request, pk):
    new_layer = Layer.objects.get(pk=pk)
    new_layer.pk = None
    # find the last postion:
    layers = [x.pos for x in Layer.objects.filter(site__id=Layer.objects.get(pk=pk).site.pk).all()]
    last = max(layers)
    new_layer.pos = last+1
    new_layer.save()
    layer = Layer.objects.get(pk=pk)
    for profile in layer.profile.all():
        new_layer.profile.add(profile)
    for ref in layer.ref.all():
        new_layer.ref.add(ref)
    for cp in layer.checkpoint.all():
        new_layer.checkpoint.add(cp)
    for date in layer.date.all():
        new_layer.date.add(date)
    return JsonResponse({'pk':new_layer.pk})

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
        layers = [x.pos for x in Layer.objects.filter(site__id=profile.site.pk).all()]
        last = max(layers) if len(layers)>0 else 0
        layer = Layer(name=f"Layer {last+1}", pos=last+1, site=profile.site)
        layer.save()
        layer.profile.add(profile)
    return JsonResponse({"pk":layer.pk, 'name':layer.name})

def remove_otherlayer(request,profile_id):
    """
    remove a layer from an existing profile (dont delete the layer itself)
    """
    profile = Profile.objects.get(pk=profile_id)
    layer = Layer.objects.get(pk=int(request.GET['layer']))
    layer.profile.remove(profile)
    return JsonResponse({"pk":layer.pk, 'name':layer.name})


def update_layer_positions(request, site_id):
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

def get_description(request):
    data = request.GET.dict()
    model = models[data['model']]
    object = model.objects.get(pk=data['id'])
    if object.new_description:
        data = json.loads(object.new_description)
    else:
        data = dict({'empty':True, 'model': data['model']})
    return JsonResponse(data)

@csrf_exempt
def save_description(request):
    data = request.GET.dict()
    model = models[data['model']]
    object = model.objects.get(pk=data['id'])

    data = request.POST.dict()
    data = json.loads(data['data'])

    object.new_description = json.dumps(data)
    object.save()

    return JsonResponse({'data':True, 'redirect': reverse('site_detail', kwargs={'pk': object.id})})