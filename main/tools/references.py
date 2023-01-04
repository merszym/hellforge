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
