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
def update_positions(request, pk):
    junction = ProfileLayerJunction.objects.get(pk=pk)
    profile = junction.profile

    all_junctions = ProfileLayerJunction.objects.filter(profile=profile)

    positions = [x.position for x in all_junctions]
    
    junction_pos = junction.position
    junction_index = positions.index(junction_pos) #the relative position of the junction
    

    # do some basic checking: already at top?
    if not junction_index == 0:
        # now get the index of the layer to switch positions with
        n = junction_index - 1
        swap_junction = all_junctions[n]
        swap_pos = swap_junction.position

        # and swap positions
        junction.position = swap_pos
        swap_junction.position = junction_pos

        # and save
        junction.save()
        swap_junction.save()

    from main.tools.profile import get_profile_detail

    context = {"profile": f"profile_{profile.pk}"}

    request.GET._mutable = True
    request.GET.update(context)

    return get_profile_detail(request)


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
    path("positions/<int:pk>", update_positions, name="main_layer_positionupdate"),
]
