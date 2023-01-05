from django.urls import path
from django.db.models import Q
from django.shortcuts import render
from main.models import Epoch

def render_search_results(request):
    kw = request.POST.get('keyword')
    q = Epoch.objects.filter(Q(name__contains=kw) | Q(description__contains=kw ))
    return render(request, 'main/epoch/epoch-searchresults.html', context={'object_list':q})

urlpatterns = [
    path('search', render_search_results,  name='ajax_epoch_search'),
]