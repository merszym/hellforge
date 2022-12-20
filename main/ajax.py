from .forms import ReferenceForm, ProfileForm, DateForm, ContactForm, RelDateForm
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from .models import Reference, Location, Site, Profile, Layer, Culture, Epoch, Checkpoint, ContactPerson, Image, Gallery, DatingMethod
from django.db.models import Q
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import models

def download_header(request):
    from django.core.files.base import ContentFile
    import pandas as pd

    model = models[request.GET.get('model')]
    cols = model.table_columns()
    df = pd.DataFrame(columns=cols)

    file_to_send = ContentFile(df.to_csv(index=False))
    response = HttpResponse(file_to_send,'application/octet-stream')

    return response


def fill_modal(request):
    choice = request.GET.get('type', False)
    if choice=='dating':
        html = render(request,'main/dating/dating-modal-content.html',{'datingoptions': DatingMethod.objects.all()})
    if choice=='reldate':
        html = render(request,'main/dating/reldate-modal-content.html', {'form': RelDateForm(request.POST)})
    if choice=='culture':
        html = render(request,'main/culture/culture-modal-content.html')
    return html


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

def save_culture(request):
    if pk := request.POST.get('culture',False):
        if dat := request.POST.get('info', False):
            model,mpk = dat.split(',')
            model = models[model].objects.get(pk=int(mpk))
            model.culture = Culture.objects.get(pk=int(pk))
            model.save()
            return JsonResponse({"status":True})
    return render(request,'main/culture/culture-modal-content.html')

@csrf_exempt
def search_ref(request):
    kw = request.POST.get('keyword')
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

def get_description(request):
    data = request.GET.dict()
    model = models[data['model']]
    object = model.objects.get(pk=data['id'])
    if object.description:
        data = json.loads(object.description)
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

    object.description = json.dumps(data)
    object.save()

    return JsonResponse({'data':True, 'redirect': reverse('site_detail', kwargs={'pk': object.id})})