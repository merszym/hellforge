from .forms import ReferenceForm
from django.http import JsonResponse
from .models import Reference
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

def save_ref(request):
    form = ReferenceForm(request.POST)
    if form.is_valid():
        obj = form.save()
        obj.refresh_from_db()
        return JsonResponse({"pk":obj.id, 'title':obj.title, 'short':obj.short})
    return JsonResponse({"pk":False})

@csrf_exempt
def search_ref(request):
    data = {x:v[0] for (x,v) in dict(request.POST).items()}
    kw = data['keyword']
    q = Reference.objects.filter(Q(short__contains=kw) | Q(title__contains=kw ))
    return JsonResponse({x.pk:f"{x.short};;{x.title}" for x in q})