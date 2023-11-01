from .forms import ReferenceForm, DateForm, ContactForm
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from .models import (
    Reference,
    Location,
    Site,
    Profile,
    Layer,
    Culture,
    Epoch,
    Person,
    Image,
    Gallery,
    DatingMethod,
    Description,
)
from django.db.models import Q
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import models
from main.tools.generic import get_instance_from_string, download_csv


def download_header(request):
    from django.core.files.base import ContentFile
    import pandas as pd

    model = models[request.GET.get("model")]
    cols = model.table_columns()
    df = pd.DataFrame(columns=cols)

    return download_csv(df)


# belongs into site, layer or profile tools
def fill_modal(request):
    choice = request.GET.get("type", False)
    object = get_instance_from_string(request.GET.get("instance"))

    if choice == "layer_edit":
        options = Layer.objects.filter(Q(site=object.site)).exclude(id=object.pk)
        if object.parent:
            options = options.exclude(id=object.parent.pk)
        html = render(request, "main/layer/layer-edit-modal.html", {"object": object, "parent_options": options})
    if choice == "layer_properties":
        html = render(request, "main/layer/layer-properties-modal.html", {"object": object, "origin": "layer"})
    if choice == "dating":
        html = render(
            request,
            "main/dating/dating-modal-content.html",
            {"datingoptions": DatingMethod.objects.all(), "origin": "form"},
        )
    if choice == "culture":
        html = render(request, "main/culture/culture-parent-modal.html", {"object": object, "origin": "culture"})
    if choice == "site_contact":
        html = render(request, "main/site/site-contact-modal.html", {"object": object, "origin": "site"})
    if choice == "date-list":
        html = render(request, "main/dating/dating-list-modal.html", {"object": object, "origin": "layer"})
    return html


@csrf_exempt
def upload_url(request):
    url = json.loads(request.body).get("url")
    res = {
        "success": 1,
        "file": {
            "url": url,
        },
    }
    return JsonResponse(res)


@csrf_exempt
def upload_image(request):
    description = Description.objects.get(pk=int(request.GET.get("id")))

    try:
        gallery = description.gallery
    except:  # gallery doesnt exist yet
        gallery = Gallery(description=description)
        gallery.save()

    image = Image(image=request.FILES.get("image"), gallery=gallery)
    image.save()
    image.refresh_from_db()

    if image.pk:
        success = 1
        url = image.image.url
    else:
        success = 0
        url = ""

    res = {
        "success": success,
        "file": {
            "url": url,
        },
    }
    return JsonResponse(res)


def save_contact(request):
    form = ContactForm(request.POST)
    if form.is_valid():
        obj = form.save()
        obj.refresh_from_db()
        return JsonResponse({"pk": obj.id, "name": obj.name})
    return JsonResponse({"pk": False})


@csrf_exempt
def search_contact(request):
    data = {x: v[0] for (x, v) in dict(request.POST).items()}
    kw = data["keyword"]
    q = Person.filter(kw)
    return JsonResponse({x.pk: f"{x.name}" for x in q})


@csrf_exempt
def search_loc(request):
    data = {x: v[0] for (x, v) in dict(request.POST).items()}
    kw = data["keyword"]
    q = Location.objects.filter(Q(name__contains=kw))
    return JsonResponse({x.pk: x.name for x in q})
