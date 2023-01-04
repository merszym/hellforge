from main.models import models
from django.http import JsonResponse

def get_instance_from_string(string):
    # Get the primary key of the model from the data
    # return the instance
    model, pk = string.split('_')
    return models[model].objects.get(pk=int(pk))

def set_x_to_y_fk(request, field):
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
        return JsonResponse({"status":True})
    return JsonResponse({"status":False})

def add_x_to_y_m2m(request, field):
    m1 = get_instance_from_string(request.POST.get('instance_x'))
    m2 = get_instance_from_string(request.POST.get('instance_y'))
    if m1 and m2:
        getattr(m2, field).add(m1)
        return JsonResponse({'status': True})
    else:
        return JsonResponse({'status': False})

def remove_x_from_y_m2m(request, field):
    m1 = get_instance_from_string(request.POST.get('instance_x'))
    m2 = get_instance_from_string(request.POST.get('instance_y'))
    if m1 and m2:
        getattr(m2, field).remove(m1)
        return JsonResponse({'status': True})
    else:
        return JsonResponse({'status': False})

def delete_x(request):
    """
    A generic function to delete an object
    """
    m1 = get_instance_from_string(request.POST.get('instance_x'))
    m1.delete()
    return JsonResponse({'status':True})
