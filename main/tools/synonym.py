from main.tools.generic import add_x_to_y_m2m, delete_x, get_instance_from_string
from main.models import Synonym
from django.urls import path
import copy


def create_and_add(request):
    """
    create a synonym and add it to the object in the request
    """
    object = get_instance_from_string(request.POST.get("object"))

    name = request.POST.get("name")
    type = request.POST.get("type")

    synonym = Synonym(name=name, type=type)
    synonym.save()
    synonym.refresh_from_db()

    object.synonyms.add(synonym)

    # now return the right modal
    request.GET._mutable = True

    if object.model == "layer":
        type = "edit"
    elif object.model == "sample":
        type = "edit_synonyms"

    request.GET.update({"object": f"{object.model}_{object.pk}", "type": type})

    from main.ajax import get_modal

    return get_modal(request)


urlpatterns = [
    path("add", create_and_add, name="main_synonym_add"),
    path("delete", delete_x, name="main_synonym_delete"),
]
