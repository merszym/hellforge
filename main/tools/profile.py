from django.http import JsonResponse
from django.urls import path
from main.models import Layer
from main.tools.generic import add_x_to_y_m2m, get_instance_from_string
from django.contrib.auth.decorators import login_required  # this is for now, make smarter later
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

    # now alter the request to use the generic add_x_to_y_m2m function
    post = request.POST.copy()
    post["instance_x"] = f"layer_{layer.pk}"

    # Create a mutable copy of the request object
    # set the POST parameter
    new_request = copy.copy(request)
    new_request.POST = post
    return add_x_to_y_m2m(new_request)


# and add the urls
urlpatterns = [
    path("add-layer", create_layer, name="main_profile_layer_add"),
]
