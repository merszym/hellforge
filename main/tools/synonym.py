from main.forms import SynonymForm
from main.models import models, Synonym
from django.http import JsonResponse
from django.shortcuts import render

def add(request):
    form = SynonymForm(request.POST)
    if form.is_valid():
        obj = form.save()
        model = request.POST.get('model', False)
        model_pk = request.POST.get('modelpk', False)
        if model and model_pk:
            model = models[model].objects.get(pk=int(model_pk))
            model.synonyms.add(obj)
            return JsonResponse({'status':True})
    return JsonResponse({'status':False})


def remove(request):
    if request.POST:
        if pk := request.POST.get('pk', False):
            Synonym.objects.get(pk=int(pk)).delete()
            return JsonResponse({'status':True})
    return JsonResponse({'status':False})