from django.urls import path
from main.models import Layer, ProfileLayerJunction
from main.tools.generic import get_instance_from_string
from django.contrib.auth.decorators import login_required


@login_required
def remove_layer_from_profile(request, layer, profile):
    profile = get_instance_from_string(f"profile_{profile}")
    layer = get_instance_from_string(f"layer_{layer}")

    # Add layer to the profile
    getattr(profile, "layer").remove(layer)

    # render the updated profile
    from main.tools.site import get_site_profile_tab

    request.GET._mutable = True
    request.GET.update(
        {"site": f"site_{profile.site.pk}", "profile": f"profile_{profile.pk}"}
    )

    return get_site_profile_tab(request)


@login_required
def add_layer_to_profile(request, layer, profile):
    profile = get_instance_from_string(f"profile_{profile}")
    layer = get_instance_from_string(f"layer_{layer}")

    # Add layer to the profile
    getattr(profile, "layer").add(layer)

    # render the updated profile
    from main.tools.site import get_site_profile_tab

    request.GET._mutable = True
    request.GET.update(
        {"site": f"site_{profile.site.pk}", "profile": f"profile_{profile.pk}"}
    )

    return get_site_profile_tab(request)


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

    ProfileLayerJunction(profile=profile, layer=layer, position=position).save()

    return add_layer_to_profile(request, layer.pk, profile.pk)


# and add the urls
urlpatterns = [
    path("create-layer", create_layer, name="main_profile_layer_create"),
    path(
        "add/<int:layer>/<int:profile>",
        add_layer_to_profile,
        name="main_profile_layer_add",
    ),
    path(
        "remove/<int:layer>/<int:profile>",
        remove_layer_from_profile,
        name="main_profile_layer_remove",
    ),
]
