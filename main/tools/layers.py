from django.http import JsonResponse
from django.urls import path, reverse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DeleteView, UpdateView
from main.models import Layer, Profile, Site, Culture, models
from main.forms import ReferenceForm
from django.contrib.auth.decorators import login_required  # this is for now, make smarter later
from django.contrib.auth.mixins import LoginRequiredMixin  # this is for now, make smarter later
from main.tools.generic import add_x_to_y_m2m, get_instance_from_string, set_x_fk_to_y
import copy


@login_required
def clone(request, pk):
    new_layer = Layer.objects.get(pk=pk)
    layer = Layer.objects.get(pk=pk)
    new_layer.pk = None
    # find the last postion:
    layers = [x.pos for x in Layer.objects.filter(site__id=Layer.objects.get(pk=pk).site.pk).all()]
    new_layer.pos = max(layers) + 1
    new_layer.save()
    for profile in layer.profile.all():
        new_layer.profile.add(profile)
    for ref in layer.ref.all():
        new_layer.ref.add(ref)
    return JsonResponse({"pk": new_layer.pk})


@login_required
def update_positions(request, site_id):
    site = Site.objects.get(pk=site_id)
    ids = request.POST.get("ids").split(",")
    positions = request.POST.get("positions").split(",")  # these are the old positions, but in new order
    for pk, pos in zip(ids, sorted(positions, key=lambda x: int(x))):
        layer = site.layer.get(pk=int(pk))
        if layer.pos == int(pos):
            continue  # skip the ones that are already in the right position
        layer.pos = int(pos)
        layer.save()
    return JsonResponse({"data": True})


@login_required
def set_name(request):
    object = get_instance_from_string(request.POST.get("instance_x"))
    object.name = request.POST.get("name")
    object.unit = request.POST.get("unit", None)
    object.save()
    return JsonResponse({"status": True})


@login_required
def set_bounds(request):
    object = get_instance_from_string(request.POST.get("instance_x"))
    try:
        object.set_upper = int(request.POST.get("upper"))
    except ValueError:
        object.set_upper = None
    try:
        object.set_lower = int(request.POST.get("lower"))
    except ValueError:
        object.set_lower = None
    object.save()
    return JsonResponse({"status": True})


# and the respective urlpatterns
urlpatterns = [
    path("set-name", set_name, name="main_layer_setname"),
    path("set-bounds", set_bounds, name="main_layer_setbounds"),
    path("clone/<int:pk>", clone, name="main_layer_clone"),
    path("positions/<int:site_id>", update_positions, name="main_layer_positionupdate"),
]
