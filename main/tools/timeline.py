from django.urls import path
from django.shortcuts import render
from main.tools.site import get_timeline_data


def render_timeline(request, model, pk):
    context = {}
    if model == "site":
        context = get_timeline_data(
            pk, curves=request.GET.get("curves", False), request=request
        )
    return render(request, "main/timeline/timeline.html", context)


urlpatterns = [
    path("render/<str:model>/<int:pk>", render_timeline, name="main_timeline_render")
]
