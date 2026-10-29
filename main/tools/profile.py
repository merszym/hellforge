from django.urls import path
from django.shortcuts import render
from main.models import Layer, ProfileLayerJunction, Profile
from main.tools.generic import get_instance_from_string
from django.contrib.auth.decorators import login_required


@login_required
def update_visibility(request, pk):
    profile = Profile.objects.get(pk=pk)
    profile.visible = not profile.visible
    profile.save()

    # render the updated profile
    request.GET._mutable = True
    request.GET.update(
        {"profile": f"profile_{profile.pk}"}
    )

    return get_profile_detail(request)


# what the layer rows (layer-tablecells.html) display, loaded in bulk instead of per row.
# layer is the parent layer, the highest layer is set by attach_highest_layers
LAYER_ROW_RELATED = ["culture", "epoch", "date_upper", "date_lower", "layer"]
LAYER_ROW_PREFETCH = ["synonyms", "date", "additional_cultures"]


def layers_for_table(queryset, prefix=""):
    """
    add the related objects of the layer-table rows to a Layer (or with prefix='layer__' a ProfileLayerJunction) queryset
    """
    return queryset.select_related(*[prefix + x for x in LAYER_ROW_RELATED]).prefetch_related(
        *[prefix + x for x in LAYER_ROW_PREFETCH]
    )


def attach_highest_layers(layers):
    """
    set the highest parent layer (Layer.get_highest) of all layers with one query (from the paths)
    """
    layers = list(layers)
    highest = Layer.objects.in_bulk({layer.path_ids[0] for layer in layers if layer.path_ids})
    for layer in layers:
        if layer.path_ids:
            layer._highest = highest.get(layer.path_ids[0])
    return layers


def get_profile_detail(request):
    """
    the content of the profile that is rendered when selecting a profile and on load of the site-stratigraphy section
    important: profile is in the request.GET as soon as one clicked a profile, so by default, it is the _first_
    """
    try:
        profile = get_instance_from_string(request.GET.get('profile'))
    except AttributeError: #profile is not in the request
        profile = get_instance_from_string(request.GET.get('site')).profile.first()

    junctions = list(layers_for_table(profile.layer_junction.all(), prefix="layer__"))
    attach_highest_layers(junction.layer for junction in junctions)
    # the number of nested parents reserves the columns in the profile-table
    max_parents = profile.max_number_of_parents

    return render(
        request,
        "main/profile/profile-detail.html",
        {'object': profile, 'junctions': junctions, 'parents': range(1, max_parents)},
    )


@login_required
def add_layer_to_profile(request, layer):
    """
    Add an existing layer to an existing profile.
    - create a new instance of ProfileLayerJunction with the correct position!
    """
    profile = get_instance_from_string(request.POST.get('instance_x'))
    layer = get_instance_from_string(f"layer_{layer}")

    all_layers = [x.position for x in ProfileLayerJunction.objects.filter(profile=profile).all()]
    last = max(all_layers) if len(all_layers) > 0 else 0
    position = last + 1

    ProfileLayerJunction(profile=profile, layer=layer, position=position).save()

    # render the updated profile
    request.GET._mutable = True
    request.GET.update(
        {"profile": f"profile_{profile.pk}"}
    )

    return get_profile_detail(request)


@login_required
def create_layer(request):
    """
    create a new layer and add it to an existing profile.
    - create a new instance of ProfileLayerJunction with the correct position!
    
    in the request.POST:
    instance_y = the profile
    """
    profile = get_instance_from_string(request.POST.get("instance_y"))

    all_layers = [x.position for x in ProfileLayerJunction.objects.filter(profile=profile).all()]
    last = max(all_layers) if len(all_layers) > 0 else 0
    position = last + 1
    layer = Layer(name=f"Layer {last+1}", site=profile.site)
    layer.save()
    layer.refresh_from_db()

    #add the layer to the profile
    ProfileLayerJunction(profile=profile, layer=layer, position=position).save()

    # render the updated profile
    from main.tools.site import get_site_profile_tab

    request.GET._mutable = True
    request.GET.update(
        {"site": f"site_{profile.site.pk}", "profile": f"profile_{profile.pk}"}
    )

    return get_site_profile_tab(request)


# and add the urls
urlpatterns = [
    path("create-layer", create_layer, name="main_profile_layer_create"),
    path(
        "add/<int:layer>",
        add_layer_to_profile,
        name="main_profile_layer_add",
    ),
    path('get', get_profile_detail ,name='main_profile_get'),
    path('visibility/<int:pk>', update_visibility, name='main_profile_visibiliy')
]
