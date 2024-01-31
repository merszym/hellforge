from django.http import JsonResponse
from django.urls import path
from main.models import Layer
from main.tools.generic import add_x_to_y_m2m, get_instance_from_string
from django.contrib.auth.decorators import (
    login_required,
)  # this is for now, make smarter later
import copy


@login_required
def create_layer(request):
    """
    add a new layer to an existing profile. If the specified layer was not in the request, create it!
    instance_x = the layer / None
    instance_y = the profile
    """
    profile = get_instance_from_string(request.POST.get("instance_y"))
    all_layers = [x.pos for x in Layer.objects.filter(site__id=profile.site.pk).all()]
    last = max(all_layers) if len(all_layers) > 0 else 0
    layer = Layer(name=f"Layer {last+1}", pos=last + 1, site=profile.site)
    layer.save()

    # Add layer to the profile
    getattr(profile, "layer").add(layer)

    # render the updated profile
    from main.tools.site import get_site_profile_tab

    request.GET._mutable = True
    request.GET.update(
        {"site": f"site_{profile.site.pk}", "profile": f"profile_{profile.pk}"}
    )

    return get_site_profile_tab(request)


# and add the urls
urlpatterns = [
    path("add-layer", create_layer, name="main_profile_layer_add"),
]
