from .forms import ReferenceForm, DateForm, ContactForm, SampleBatchForm, ProfileForm, LayerColourForm
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
    AnalyzedSample,
    SampleBatch,
    Sample
)
from django.db.models import Q
from django.urls import reverse, path
from django.views.decorators.csrf import csrf_exempt
import json
from .models import models
from main.tools.generic import get_instance_from_string, download_csv
from main.tools.analyzed_samples import update_query_for_negatives
import pandas as pd

def download_header(request):
    from django.core.files.base import ContentFile
    import pandas as pd

    model = models[request.GET.get("model")]
    cols = model.table_columns()
    df = [{x:None for x in cols}]

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

    # Add sample edit context
    if object.model == "sample":
        if context["type"] == "dates_list":
            context.update({"site_dates": object.get_layer.site.get_dates() if object.get_layer else []})
        if context["type"] == "dates":
            context.update({"datingoptions": DatingMethod.objects.all()})
            context.update({"site_dates": object.get_layer.site.get_dates() if object.get_layer else []})
        if context["type"] == "edit_batch":
            context.update(
                {"site_batches": SampleBatch.objects.filter(site=object.site)}
            )
        if context["type"] == "edit_base":
            context.update(
                {
                "group_choices": set(Sample.objects.filter(domain='archaeology').values_list('hominin_group', flat=True))
                }
            )
        if context["type"] == "edit_provenience":
            try:
                provenience = json.loads(object.provenience)
            except TypeError:
                # empty provenience array so far
                provenience = {}
            context.update({"provenience": provenience})
        if context['type'] == 'edit_layer':
            fossils = Sample.objects.filter(site=object.site, domain='archaeology')
            context.update({
                'fossils':fossils
            })

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
                {
                    "datingoptions": DatingMethod.objects.all(), 
                    "origin": "form",
                }
            )
        if context["type"] == "dates_list":
            # Add dates as the layer boundaries
            context.update(
                {
                    "site_dates": object.site.get_dates(),
                    "layeroptions": Layer.objects.filter(Q(site=object.site)).exclude(id=object.pk)
                }
            )

        if context["type"] == "properties":
            context.update(
                {
                    "cultures": Culture.objects.all().order_by("name"),
                    "epochs": Epoch.objects.all().order_by("name"),
                }
            )
        if context["type"] == "colour":
            if not 'form' in request.GET:
                context.update(
                    {
                        'form':LayerColourForm(instance=object)
                    }
                )
            else:
                context.update(
                    {
                        'form':request.GET.get('form')
                    }
                )
    if object.model == "site":
        if context["type"] in ["quicksand_upload","matthias_upload"]:
            context.update(
                {
                    "seqpool":request.GET.get('seqpool',''),
                    "seqrun":request.GET.get('seqrun',''),
                    "lane":request.GET.get('lane',''),
                    "seqruns": sorted(
                        list(
                            set(
                                x.seqrun
                                for x in update_query_for_negatives(
                                    AnalyzedSample.objects.filter(sample__site=object)
                                )
                            )
                        )
                    )
                }
            )

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
    
    if object.model == 'quicksand':
        if context["type"] == "details":
            data = [x[0] for x in json.loads(object.data).values()]
            table = pd.DataFrame(
                data
            )
            for col in [
                    'RG','ReadsFiltered',
                    'ExtractLVL','ReadsExtracted','Kmers',
                    'KmerCoverage','KmerDupRate', 'Reference','ProportionMapped' 
                ]:
                try:
                    table.drop(col, axis=1, inplace=True)
                except KeyError:
                    pass
            context.update({
                'table':table.sort_values('ReadsMapped', ascending=False).to_html(index=False, classes="table table-striped")
            })
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

    if type == "quicksand":
        from main.tools.quicksand import handle_quicksand_report

        return handle_quicksand_report(request, file)

    if type == "matthias":
        from main.tools.matthias import handle_file_upload

        return handle_file_upload(request, file)

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
