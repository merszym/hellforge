from django.http import JsonResponse
from django.urls import path, reverse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DeleteView, UpdateView
from main.models import Layer, Profile, Site, Culture, models, Epoch
from main.forms import ReferenceForm
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
def clone(request, pk):
    new_layer = Layer.objects.get(pk=pk)
    layer = Layer.objects.get(pk=pk)
    new_layer.pk = None
    # find the last postion:
    new_layer.pos = max([x.pos for x in Layer.objects.filter(site=layer.site)]) + 1
    new_layer.save()

    for profile in layer.profile.all():
        new_layer.profile.add(profile)

    for ref in layer.ref.all():
        new_layer.ref.add(ref)

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

    request.GET._mutable = True
    request.GET.update({"object": f"layer_{object.pk}", "type": "dates_list"})

    return get_modal(request)


@login_required
def set_date(request):
    from main.models import Date

    ## RULES ##
    # 1. If both upper and lower dates are set
    # - upper can be infinite
    # - lower cant be infinite
    #
    # 2. If only one date is set
    # - only upper and infinite --> has no meaning, so dont allow
    # - only upper --> Younger than that
    # - only lower --> Older than that (so lower can also be infinite in this case)

    object = get_instance_from_string(request.POST.get("instance_x"))

    try:
        date_upper = Date.objects.get(pk=int(request.POST.get("upper_date")))
    except ValueError:
        date_upper = None

    try:
        date_lower = Date.objects.get(pk=int(request.POST.get("lower_date")))
    except ValueError:
        date_lower = None

    # now check for the rules
    errors = []
    if date_upper and date_lower:
        if date_lower.get_upper().startswith(">"):
            errors.append(
                f"No infinite Date ({date_lower}) allowed as lower date, if upper date exists"
            )
    elif date_upper and not date_lower and date_upper.get_upper().startswith(">"):
        errors.append(
            f"No infinite Date ({date_upper}) allowed as only upper date. Younger than infinite is not meaningful"
        )

    if len(errors) == 0:
        object.date_upper = date_upper
        object.date_lower = date_lower
        object.save()

    request.GET._mutable = True
    request.GET.update(
        {
            "object": f"layer_{object.pk}",
            "type": "dates_list",
            "errors": errors if len(errors) > 0 else None,
        }
    )

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
    path("set-name", set_name, name="main_layer_setname"),
    path("set-culture", set_culture, name="layer-culture-update"),
    path("set-epoch", set_epoch, name="layer-epoch-update"),
    path("set-bounds", set_bounds, name="main_layer_setbounds"),
    path("set-date", set_date, name="layer-setdate-update"),
    path("clone/<int:pk>", clone, name="main_layer_clone"),
    path("positions", update_positions, name="main_layer_positionupdate"),
]
