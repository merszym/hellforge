from main.models import models
from django.http import JsonResponse

def get_instance_from_string(string):
    # Get the primary key of the model from the data
    # return the instance
    model, pk = string.split('_')
    return models[model].objects.get(pk=int(pk))

def set_x_to_y_fk(request, field, response=True):
    """
    set the foreign key of x to y
    x = profile
    y = site
    field = profile
    --
    profile.site = site
    """
    x = get_instance_from_string(request.POST.get('instance_x'))
    y = get_instance_from_string(request.POST.get('instance_y'))
    if x and y:
        setattr(x, field, y)
        x.save()
        return JsonResponse({"status":True}) if response else (True,x,y)
    return JsonResponse({"status":False}) if reponse else (False, x,y)

def add_x_to_y_m2m(request, field, response=True):
    x = get_instance_from_string(request.POST.get('instance_x'))
    y = get_instance_from_string(request.POST.get('instance_y'))
    if x and y:
        getattr(y, field).add(x)
        return JsonResponse({'status': True}) if response else (True,x,y)
    else:
        return JsonResponse({'status': False}) if response else (False,x,y)

def remove_x_from_y_m2m(request, field, response=True):
    x = get_instance_from_string(request.POST.get('instance_x'))
    y = get_instance_from_string(request.POST.get('instance_y'))
    if x and y:
        getattr(y, field).remove(x)
        return JsonResponse({'status': True}) if response else (True,x,y)
    else:
        return JsonResponse({'status': False}) if response else (False,x,y)

def delete_x(request, response=True):
    """
    A generic function to delete an object
    """
    x = get_instance_from_string(request.POST.get('instance_x'))
    x.delete()
    return JsonResponse({'status':True}) if response else True