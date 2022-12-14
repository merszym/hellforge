from main.models import Reference, models
import numpy as np
from django.db.models import Q
from django.shortcuts import render

def find(kw):
    #find the best reference for a given search term
    if kw==kw:
        if ref := Reference.objects.filter(Q(short=kw) | Q(doi=kw)).first():
                return ref
        return 'Not Found'
    return np.nan

def get_modal(request):
    return render(request, 'main/references/reference-search.html')


def add_to_model(request):
    from django.http import JsonResponse

    pk = request.POST.get('pk', False)
    model = request.POST.get('model', False)
    model_pk = request.POST.get('modelpk', False)
    if pk and model and model_pk:
        ref = Reference.objects.get(pk=int(pk))
        model = models[model].objects.get(pk=int(model_pk))
        model.ref.add(ref)
        return JsonResponse({'status':True})
    return JsonResponse({'status':False})


def get_popup(request):
    pk = request.GET.get('pk', False)
    obj = Reference.objects.get(pk=int(pk))
    context = {'ref': obj, 'pos':'right'}

    if title := request.GET.get('title', False):
        context.update({'title':title})
    return render(request, 'main/references/reference-popup.html', context)

def get_tablerow(request):
    pk = request.GET.get('pk', False)
    obj = Reference.objects.get(pk=int(pk))
    context = {'ref': obj}
    return render(request, 'main/references/reference-tablerow.html', context)
