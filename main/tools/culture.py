from django.urls import path
from django.db.models import Q
from django.shortcuts import render
from django.http import JsonResponse
from main.models import Culture

def render_search_results(request):
    kw = request.POST.get('keyword')
    q = Culture.objects.filter(Q(name__contains=kw) | Q(description__contains=kw ))
    return render(request, 'main/culture/culture-searchresults.html', context={'object_list':q})

urlpatterns = [
    path('search', render_search_results,  name='ajax_culture_search'),
]