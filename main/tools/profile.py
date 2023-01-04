from django.http import JsonResponse
from django.urls import path, reverse
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import DeleteView
from main.models import Profile, Site, Layer
from main.tools.generic import add_x_to_y_m2m, get_instance_from_string, remove_x_from_y_m2m, delete_x
import copy

def get(request, pk):
    return render(request,'main/profile/profile-detail.html', {'object': Profile.objects.get(pk=pk)})

def add_layer(request):
    """
    add a new layer to an existing profile. If the specified layer was not in the request, create it!
    instance_x = the layer / None
    instance_y = the profile
    """
    if request.POST.get('instance_x', False):
        return add_x_to_y_m2m(request, 'layer')
    else:
        profile = get_instance_from_string(request.POST.get('instance_y'))
        all_layers = [x.pos for x in Layer.objects.filter(site__id=profile.site.pk).all()]
        last = max(all_layers) if len(all_layers)>0 else 0
        layer = Layer(name=f"Layer {last+1}", pos=last+1, site=profile.site)
        layer.save()

        #now alter the request to use the generic add_x_to_y_m2m function
        post = request.POST.copy()
        post['instance_x'] = f'layer_{layer.pk}'

        # Create a mutable copy of the request object
        # set the POST parameter
        new_request = copy.copy(request)
        new_request.POST = post
        return add_x_to_y_m2m(new_request, 'layer')


def remove_layer(request):
    """
    remove a layer from an existing profile (dont delete the layer itself)
    instance_x = the layer
    instance_y = the profile
    """
    return remove_x_from_y_m2m(request, 'layer')

# and add the urls
urlpatterns = [
    path('get/<int:pk>',  get,          name='main_profile_get'),
    path('add-layer',     add_layer,    name='main_profile_layer_add'),
    path('remove-layer',  remove_layer, name='main_profile_layer_remove'),
    path('delete',        delete_x,     name='main_profile_delete'),
]