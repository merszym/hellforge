from .forms import ReferenceForm, DateForm, ContactForm, SampleBatchForm
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from .models import (
    Reference,
    Location,
    Site,
    Profile,
    Layer,
    Culture,
    Person,
    Image,
    Gallery,
    DatingMethod,
    Description,
    Date,
    SampleBatch,
)
from django.db.models import Q
from django.urls import reverse, path
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


def get_modal_context(object, request):
    context = {"object": object, "type": request.GET.get("type", "")}

    # Add layer edit context
    if object.model == "layer" and context["type"] == "edit":
        options = Layer.objects.filter(Q(site=object.site)).exclude(id=object.pk)
        if object.parent:
            options = options.exclude(id=object.parent.pk)
        context.update({"parent_options": options})
    # Add layer date context
    if object.model == "layer" and context["type"] == "dates":
        context.update({"datingoptions": DatingMethod.objects.all(), "origin": "form"})

    # For adding sample-batches
    if object.model == "site" and context["type"] == "add_samplebatch":
        context.update(
            {
                "samplebatch_form": SampleBatchForm,
            }
        )
    return context


# this is for the modals
# return the rendered html for the requested modal
def get_modal(request):
    object = get_instance_from_string(request.GET.get("object"))
    model = object.model
    context = get_modal_context(object, request)
    # get additional context
    return render(request, f"main/modals/{model}_modal.html", context)


# belongs into site, layer or profile tools
def fill_modal(request):
    choice = request.GET.get("type", False)
    object = get_instance_from_string(request.GET.get("instance"))
    if choice == "culture":
        html = render(
            request,
            "main/culture/culture-parent-modal.html",
            {"object": object, "origin": "culture"},
        )
    if choice == "date-list":
        html = render(
            request,
            "main/dating/dating-list-modal.html",
            {"object": object, "origin": "layer"},
        )
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
    try:
        file = request.FILES.get("image")
    except:
        file = request.FILES.get("file")
    if gal := request.POST.get("instance_x", False):
        gallery = get_instance_from_string(gal)
    else:
        description = Description.objects.get(pk=int(request.GET.get("id")))
        try:
            gallery = description.gallery
        except:  # gallery doesnt exist yet
            gallery = Gallery(description=description)
            gallery.save()

    image = Image(image=file, gallery=gallery)
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


urlpatterns = [
    path("modal", get_modal, name="main_modal_get"),
]
