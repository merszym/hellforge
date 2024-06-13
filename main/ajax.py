from .forms import ReferenceForm, DateForm, ContactForm, SampleBatchForm, ProfileForm
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from .models import (
    Location,
    Layer,
    Person,
    Image,
    Gallery,
    DatingMethod,
    Description,
    Culture,
    Epoch,
    Date,
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
    context = {
        "object": object,
        "type": request.GET.get("type", ""),
        "origin": request.GET.get("origin", ""),
        "errors": request.GET.get("errors", None),
    }
    if context["errors"] == "[]":
        context.update({"errors": None})

    # Add layer edit context
    if object.model == "layer":
        if context["type"] == "edit":
            # basic edit modal
            options = Layer.objects.filter(Q(site=object.site)).exclude(id=object.pk)
            if object.parent:
                options = options.exclude(id=object.parent.pk)
            context.update({"parent_options": options})
        if context["type"] == "dates":
            # Add a date to the layer
            context.update(
                {"datingoptions": DatingMethod.objects.all(), "origin": "form"}
            )
        if context["type"] == "dates_list":
            # Add dates as the layer boundaries
            context.update(
                {
                    "site_dates": Date.objects.filter(
                        origin_model__site=object.site
                    ).order_by("origin_model")
                }
            )
        if context["type"] == "properties":
            context.update(
                {
                    "cultures": Culture.objects.all().order_by("name"),
                    "epochs": Epoch.objects.all().order_by("name"),
                }
            )
    if object.model == "site":
        if context["type"] == "add_samplebatch":
            # Adding sample-batches to the site
            context.update(
                {
                    "samplebatch_form": SampleBatchForm,
                }
            )
        if context["type"] == "connection_form":
            # Adding sample-batches to the site
            try:
                connection = get_instance_from_string(request.GET.get("fill"))
            except ValueError:
                connection = None
            context.update({"connection": connection})
        if context["type"] == "add_profile":
            context.update({"profile_form": ProfileForm})
    if object.model == "sample":
        if context["type"] == "edit_provenience":
            try:
                provenience = json.loads(object.provenience)
            except TypeError:
                # empty provenience array so far
                provenience = {}
            context.update({"provenience": provenience})

    return context


# this is for the modals
# return the rendered html for the requested modal
def get_modal(request):
    obj_string = request.GET.get("object")
    object = get_instance_from_string(obj_string)
    model = object.model
    context = get_modal_context(object, request)
    # get additional context
    return render(request, f"main/modals/{model}_modal.html", context)


#
#
## Handle Uploads to the Page
#
#


@csrf_exempt
def upload(request):
    """
    Main upload entry point, should be called with 'file' or 'image' in request.FILES and
    'type' in request.GET. additional specific information is handled in request.POST or request.GET.
    """
    type = request.GET.get("type", None)

    # Edge-case, NO file, upload url...this is only required by editorJS
    if type == "url":
        url = json.loads(request.body).get("url")
        response = {
            "success": 1,
            "file": {
                "url": url,
            },
        }
        return JsonResponse(response)

    # now get the file
    image = request.FILES.get("image")
    file = request.FILES.get("file")

    # and handle how it is processed
    if type == "galleryimage":
        from main.tools.samples import handle_galleryimage_upload

        return handle_galleryimage_upload(request, image)

    if type == "samplebatch":
        from main.tools.samples import handle_samplebatch_file

        return handle_samplebatch_file(request, file)

    if type == "libraries":
        from main.tools.analyzed_samples import handle_library_file

        return handle_library_file(request, file)

    if type == "faunaltable":
        from main.tools.fauna import handle_faunal_table

        return handle_faunal_table(request, file)

    if type == "stratigraphy":
        from main.tools.site import handle_stratigraphy

        return handle_stratigraphy(request, file)


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
    path("upload", upload, name="main_upload"),
]
