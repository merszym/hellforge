from main.models import models
from django.http import JsonResponse
from django.urls import path
from django.shortcuts import render
from django.contrib.auth.decorators import login_required  # this is for now, make smarter later


@login_required
def search(request):
    kw = request.POST.get("keyword")
    origin = request.POST.get("origin")
    model = request.POST.get("model")
    q = models[model].filter(kw)
    return render(request, f"main/{model}/{model}-searchresults.html", context={"object_list": q, "origin": origin})


def get_instance_from_string(string):
    # Get the primary key of the model from the data
    # return the instance
    model, pk = string.split("_")
    return models[model].objects.get(pk=int(pk))


@login_required
def unset_fk(request, field, response=True):
    """
    set the foreign key relationship to None
    """
    x = get_instance_from_string(request.POST.get("instance_x"))
    if x:
        setattr(x, field, None)
        x.save()
        return JsonResponse({"status": True}) if response else (True, x)
    return JsonResponse({"status": False}) if reponse else False


@login_required
def set_x_fk_to_y(request, field, response=True):
    """
    set the foreign key of x to y
    x = profile
    y = site
    field = profile
    --
    profile.site = site
    """
    x = get_instance_from_string(request.POST.get("instance_x"))
    y = get_instance_from_string(request.POST.get("instance_y"))
    if x and y:
        setattr(x, field, y)
        x.save()
        return JsonResponse({"status": True}) if response else (True, x, y)
    return JsonResponse({"status": False}) if reponse else False


@login_required
def add_x_to_y_m2m(request, field=None, response=True):
    x = get_instance_from_string(request.POST.get("instance_x"))
    y = get_instance_from_string(request.POST.get("instance_y"))
    if not field:
        field = request.POST.get("instance_x").split("_")[0]
    if x and y:
        getattr(y, field).add(x)
        return JsonResponse({"status": True}) if response else (True, x, y)
    return JsonResponse({"status": False}) if response else (False, x, y)


@login_required
def remove_x_from_y_m2m(request, field=None, response=True):
    x = get_instance_from_string(request.POST.get("instance_x"))
    y = get_instance_from_string(request.POST.get("instance_y"))
    if not field:
        field = request.POST.get("instance_x").split("_")[0]
    if x and y:
        getattr(y, field).remove(x)
        return JsonResponse({"status": True}) if response else (True, x, y)
    return JsonResponse({"status": False}) if response else False


@login_required
def delete_x(request, response=True):
    """
    A generic function to delete an object
    """
    x = get_instance_from_string(request.POST.get("instance_x"))
    x.delete()
    return JsonResponse({"status": True}) if response else True


urlpatterns = [
    path("search", search, name="main_generic_search"),
    path("rmm2m/<str:field>", remove_x_from_y_m2m, name="main_generic_rmm2m"),
    path("rmm2m", remove_x_from_y_m2m, name="main_generic_rmm2m"),
    path("unsetfk/<str:field>", unset_fk, name="main_generic_unsetfk"),
    path("setfk/<str:field>", set_x_fk_to_y, name="main_generic_setfk"),
    path("addm2m/<str:field>", add_x_to_y_m2m, name="main_generic_addm2m"),
    path("addm2m", add_x_to_y_m2m, name="main_generic_addm2m"),
    path("deletex", delete_x, name="main_generic_delete"),
]
