from main.models import Reference, models
from main.forms import ReferenceForm
import numpy as np
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, ListView, UpdateView

def find(kw):
    #find the best reference for a given search term
    if kw==kw:
        if ref := Reference.objects.filter(Q(short=kw) | Q(doi=kw)).first():
            return ref
        return 'Not Found'
    return np.nan

def get_modal(request):
    return render(request, 'main/reference/reference-searchinput.html', {'origin':'editorjs'})

def get_popup(request):
    pk = request.GET.get('pk', False)
    obj = Reference.objects.get(pk=int(pk))
    context = {'ref': obj, 'pos':'right'}

    if title := request.GET.get('title', False):
        context.update({'title':title})
    return render(request, 'main/reference/reference-popup.html', context)

## References ##
class ReferenceCreateView(CreateView):
    model = Reference
    fields = "__all__"
    template_name = 'main/reference/reference_form.html'

class ReferenceUpdateView(UpdateView):
    model = Reference
    fields = "__all__"
    template_name = 'main/reference/reference_form.html'

urlpatterns = [
    path('modal',               get_modal,                     name='ajax_ref_modal_get'),
    path('popup',               get_popup,                     name='ajax_ref_popup_get'),
    path('create',              ReferenceCreateView.as_view(), name='ref_add'),
    path('edit/<int:pk>',       ReferenceUpdateView.as_view(), name='ref_update'),
]