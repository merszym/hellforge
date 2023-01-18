from django.urls import path
from django.shortcuts import render
from main.tools.site import get_timeline_data

def render_timeline(request, model, pk):
    context = {}
    if model == 'site':
        context = get_timeline_data(pk, hidden=request.GET.get('hidden', False), related=request.GET.get('related', False))
    return render(request, 'main/timeline/timeline.html', context)

urlpatterns = [
    path('render/<str:model>/<int:pk>', render_timeline, name='main_timeline_render')
]