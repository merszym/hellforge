from .forms import ReferenceForm, ProfileForm
from django.http import JsonResponse
from django.shortcuts import render
from .models import Reference, Location, Site, Profile
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

def save_ref(request):
    form = ReferenceForm(request.POST)
    if form.is_valid():
        obj = form.save()
        obj.refresh_from_db()
        return JsonResponse({"pk":obj.id, 'title':obj.title, 'short':obj.short})
    return JsonResponse({"pk":False})

def save_profile(request,site_id):
    form = ProfileForm(request.POST)
    print(form)
    print(site_id)
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