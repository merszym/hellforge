from django.http import JsonResponse
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

    context = {"profile": f"profile_{profile.pk}"}

    request.GET._mutable = True
    request.GET.update(context)

    from main.tools.profile import get_profile_detail

    return get_profile_detail(request)


@login_required
def update_positions(request):
    layer = get_instance_from_string(request.POST.get("object"))
    direction = request.POST.get("direction")

    all_layers = list(layer.site.layer.all())
    positions = [x.pos for x in all_layers]

    layer_index = positions.index(layer.pos)
    layer_pos = layer.pos

    # do some basic checking: already at top or aleady at bottom
    check1 = all([layer_index == 0, direction == "up"])
    check2 = all([layer_index == len(positions) - 1, direction == "down"])
    if not any([check1, check2]):
        # now get the index of the layer to switch positions with
        n = layer_index - 1 if direction == "up" else layer_index + 1
        swap_layer = all_layers[n]
        swap_pos = swap_layer.pos

        # and swap positions
        layer.pos = swap_pos
        swap_layer.pos = layer_pos

        # and save
        layer.save()
        swap_layer.save()

    from main.tools.site import get_site_profile_tab

    context = {"site": f"site_{layer.site.pk}"}

    # check if selected profile exists
    if prof := request.GET.get("profile", False):
        profile = get_instance_from_string(prof)
        context.update({"profile": f"profile_{profile.pk}"})

    request.GET._mutable = True
    request.GET.update(context)

    return get_site_profile_tab(request)


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


# and the respective urlpatterns
urlpatterns = [
    path("update/<int:pk>", update, name="main_layer_update"),
    path("set-name", set_name, name="main_layer_setname"),
    path("set-culture", set_culture, name="layer-culture-update"),
    path("set-epoch", set_epoch, name="layer-epoch-update"),
    path("clone/<int:pk>", clone, name="main_layer_clone"),
    path("positions", update_positions, name="main_layer_positionupdate"),
]
