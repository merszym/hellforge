from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.views.decorators.http import require_POST
from django.urls import path, reverse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DeleteView, UpdateView
from main.models import Layer, Profile, Site, Culture, models, Epoch, ProfileLayerJunction
from main.forms import ReferenceForm, LayerColourForm
from django.contrib.auth.decorators import (
    login_required,
)  # this is for now, make smarter later
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)  # this is for now, make smarter later
from main.tools.generic import add_x_to_y_m2m, get_instance_from_string, set_x_fk_to_y
import copy
from django.shortcuts import render
from main.ajax import get_modal


@login_required
def update(request, pk):
    # this is only for color and texture now, but I should make this a generic function for layer updates
    object = Layer.objects.get(pk=pk)
    form = LayerColourForm(request.POST, instance=object)
    if form.is_valid():
        form.save()
    
    request.GET._mutable = True
    request.GET.update({"object": f"layer_{object.pk}", "type": "colour", 'form':form})

    return get_modal(request)


@login_required
def clone(request, pk):
    """
    from the ProfileLayerJunction, get the layer.
    Clone the layer and create a new ProfileLayerJunction. Set the position +1 and move all other layers one down
    """
    junction = ProfileLayerJunction.objects.get(pk=pk)
    profile = junction.profile

    new_layer = junction.layer
    layer = junction.layer
    new_layer.pk = None
    # find the last postion:
    new_layer.name = f"{layer.name} (+)"
    new_layer.save()
    new_layer.refresh_from_db()

    ProfileLayerJunction(layer=new_layer, profile=profile, position = junction.position).save()
    
    #after cloning a layer, the cloned layer has the same position as the original layer within the profile.
    #So given a profile, reset the position-counts for each junction
    
    for n,junction in enumerate(ProfileLayerJunction.objects.filter(profile=profile)):
        junction.position = n
        junction.save()

    context = {"profile": f"profile_{profile.pk}"}

    request.GET._mutable = True
    request.GET.update(context)

    from main.tools.profile import get_profile_detail

    return get_profile_detail(request)

@login_required
def update_inherited_features(request, pk):
    """
    from the ProfileLayerJunction, get the layer.
    inherit the layers parents properties
    """
    junction = ProfileLayerJunction.objects.get(pk=pk)
    profile = junction.profile
    layer = junction.layer

    if layer.layer:
        # update date
        inf, upper, lower = layer.layer.get_upper_and_lower()
        layer.set_upper = upper
        layer.set_lower = lower
        # update culture and epoch
        layer.culture = layer.layer.culture
        layer.epoch = layer.layer.epoch
        # update colour and texture
        layer.colour = layer.layer.colour
        layer.texture = layer.layer.texture
        layer.save()

    #after cloning a layer, the cloned layer has the same position as the original layer within the profile.
    #So given a profile, reset the position-counts for each junction
    context = {"profile": f"profile_{profile.pk}"}

    request.GET._mutable = True
    request.GET.update(context)

    from main.tools.profile import get_profile_detail

    return get_profile_detail(request)

def renumber_profile(profile, junction_ids):
    """
    set the positions of the layers in a profile (0, 1, 2, ...) in the order of the junction ids.
    only this profile changes, the positions of the layers in other profiles stay
    """
    with transaction.atomic():
        for position, pk in enumerate(junction_ids):
            ProfileLayerJunction.objects.filter(pk=pk, profile=profile).update(position=position)


@login_required
@require_POST
def reorder_profile(request, pk):
    """
    the new order of the layers in a profile (drag and drop): all junction ids of the profile, top to bottom
    """
    profile = Profile.objects.get(pk=pk)
    junction_ids = [int(x) for x in request.POST.getlist("junction") if x.isdigit()]
    current = set(profile.layer_junction.values_list("pk", flat=True))
    # the complete profile, every layer once: otherwise the table is outdated (changed in the meantime)
    if len(junction_ids) != len(set(junction_ids)) or set(junction_ids) != current:
        return HttpResponse("The profile changed in the meantime, please reload it", status=409)
    renumber_profile(profile, junction_ids)
    return HttpResponse(status=204)


@login_required
@require_POST
def move_layer(request, pk):
    """
    move a layer (junction) to a position in its profile (1 = top), from the layer modal
    """
    junction = ProfileLayerJunction.objects.get(pk=pk)
    profile = junction.profile
    junction_ids = list(profile.layer_junction.order_by("position", "pk").values_list("pk", flat=True))
    try:
        position = int(request.POST.get("position"))
    except (TypeError, ValueError):
        position = junction_ids.index(junction.pk) + 1
    junction_ids.remove(junction.pk)
    junction_ids.insert(min(max(position, 1), len(junction_ids) + 1) - 1, junction.pk)
    renumber_profile(profile, junction_ids)

    # the layer modal again (with the new position), the profile-table reloads in the background
    request.GET._mutable = True
    request.GET.update({"object": f"layer_{junction.layer_id}", "type": "edit", "profile": f"profile_{profile.pk}"})
    return get_modal(request)


@login_required
def set_name(request):
    object = get_instance_from_string(request.POST.get("instance_x"))
    object.name = request.POST.get("layer-name")
    object.save()

    request.GET._mutable = True
    request.GET.update({"object": f"layer_{object.pk}", "type": "edit"})

    return get_modal(request)


@login_required
def set_culture(request):
    object = get_instance_from_string(request.POST.get("instance_x"))
    # first check if we want to set a secondary culture
    if add_culture:= request.POST.get('additional_cultures', False):
        cult = Culture.objects.get(pk=int(add_culture))
        object.additional_cultures.add(cult)
    else:
        object.culture = Culture.objects.get(pk=int(request.POST.get("culture")))
        object.save()

    request.GET._mutable = True
    request.GET.update({"object": f"layer_{object.pk}", "type": "properties"})

    return get_modal(request)


@login_required
def set_epoch(request):
    object = get_instance_from_string(request.POST.get("instance_x"))
    object.epoch = Epoch.objects.get(pk=int(request.POST.get("epoch")))
    object.save()

    request.GET._mutable = True
    request.GET.update({"object": f"layer_{object.pk}", "type": "properties"})

    return get_modal(request)

@login_required
def set_tools(request, pk):
    object = Layer.objects.get(pk=pk)
    tools = int(request.POST.get('n_tools'))
    object.n_tools = tools
    object.save()
    return JsonResponse({'success':True})


# and the respective urlpatterns
urlpatterns = [
    path("update/<int:pk>", update, name="main_layer_update"),
    path("set-name", set_name, name="main_layer_setname"),
    path("set-culture", set_culture, name="layer-culture-update"),
    path("set-epoch", set_epoch, name="layer-epoch-update"),
    path("clone/<int:pk>", clone, name="main_layer_clone"),
    path("inherit/<int:pk>", update_inherited_features, name="main_layer_inherit"),
    path("reorder/<int:pk>", reorder_profile, name="main_profile_reorder"),
    path("move/<int:pk>", move_layer, name="main_layer_move"),
    path('set-tools/<int:pk>', set_tools, name='layer_set_toolcount')
]
