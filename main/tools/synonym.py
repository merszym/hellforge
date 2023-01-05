from main.forms import SynonymForm
from main.tools.generic import add_x_to_y_m2m, delete_x
from django.urls import path
import copy

def create_and_add(request):
    """
    create a synonym and add it to a instance_y in the request
    """
    form = SynonymForm(request.POST)
    if form.is_valid():
        obj = form.save()
        #Use the generic add_to_m2m function
        post = request.POST.copy()
        post['instance_x'] = f'synonym_{obj.pk}'

        # Create a mutable copy of the request object
        # set the POST parameter
        new_request = copy.copy(request)
        new_request.POST = post
        return add_x_to_y_m2m(new_request, 'synonyms')


urlpatterns = [
    path('add',    create_and_add, name='main_synonym_add'),
    path('delete', delete_x,       name='main_synonym_delete'),
]