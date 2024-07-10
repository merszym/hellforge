from django.urls import path
from django.shortcuts import render
from main.tools.site import get_timeline_data
from main.models import Profile


def render_timeline(request, model, pk, profile=None):
    context = {}
    if profile != None:
        profile = Profile.objects.get(pk=int(profile))
        context.update({"profile": profile})
    if model == "site":
        context.update(get_timeline_data(pk, request=request, profile=profile))

    return render(request, "main/timeline/timeline.html", context)


urlpatterns = [
    path("render/<str:model>/<int:pk>", render_timeline, name="main_timeline_render"),
    path(
        "render/<str:model>/<int:pk>/<int:profile>",
        render_timeline,
        name="main_timeline_render_profile",
    ),
]
