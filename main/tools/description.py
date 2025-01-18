from main.models import Person, Author, Description, Reference, Gallery
from main.tools.generic import get_instance_from_string, delete_x
from django.http import JsonResponse,FileResponse
from django.urls import path
from django.views.generic import UpdateView
from django.views.decorators.csrf import csrf_exempt
import json
from django.urls import reverse
from django.contrib.auth.decorators import (
    login_required,
)  # this is for now, make smarter later
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)  # this is for now, make smarter later
from main.tools.generic import get_instance_from_string
from django.shortcuts import render


def print_html(request, pk):
    #print a description using weasyprint. 
    #get the html as string first, then print with weasyprint
    from weasyprint import HTML, CSS
    import io
    from django.conf import settings

    # get the required html
    html = render_description(request, pk, tostring=True)

    #get the required css
    if settings.DEBUG:
        style = CSS(str(settings.BASE_DIR) +  '/main/static/css/spectre.css')
    else:
        style = CSS(settings.STATIC_ROOT +  'css/spectre.css')

    #and write it to buffer
    buffer = io.BytesIO()

    HTML(string=html, base_url=request.build_absolute_uri()).write_pdf(buffer, stylesheets=[style])
    buffer.seek(0)

    return FileResponse(
        buffer,
        content_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=hellforge_pdf-printout.pdf"},
    )


# Get description json for detail views in editor.js
def get_description_content(request):
    description = Description.objects.get(pk=int(request.GET.get("id")))
    if hasattr(description, "gallery") == False:
        # TODO: move to signals, each description should have a Gallery by default
        tmp = Gallery(description=description)
        tmp.save()
    return JsonResponse(
        json.loads(description.content)
        if description.content
        else {"empty": True, "model": request.GET.get("model")}
    )


@csrf_exempt
def save_description(request):
    description = Description.objects.get(pk=int(request.GET.get("id")))

    data = json.loads(request.POST.get("data"))
    description.content = json.dumps(data)
    # this is used to get to the detail view of the correct model
    origin = request.POST.get("origin", None)

    # now save the site references
    ## clear the reference field
    description.ref.clear()
    for refpk in set(request.POST.get("references").split(",")):
        try:
            pk = int(refpk)
            ref = Reference.objects.get(pk=pk)
            description.ref.add(ref)
        except:  # TODO: What kind of error do I expect?
            continue

    description.save()

    if origin != "null":
        model = origin.split("_")[0]
    else:
        model = "site"

    goto = {
        "site": "site_detail",
        "project": "main_project_detail",
        "culture": "culture_detail",
    }
    model_kwargs = {
        "site": {"pk": description.content_object.id},
        "culture": {"pk": description.content_object.id},
        "project": {
            "namespace": getattr(description.content_object, "namespace", None)
        },
    }

    return JsonResponse(
        {
            "data": True,
            "redirect": reverse(goto[model], kwargs=model_kwargs[model]),
        }
    )


class DescriptionUpdateView(LoginRequiredMixin, UpdateView):
    model = Description
    template_name = "main/description/description_update.html"
    extra_context = {"readonly": False, "available_persons": Person.objects.all()}
    fields = []

    def get_context_data(self, **kwargs):
        context = super(DescriptionUpdateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


@login_required
def create_and_add_author(request):
    """
    create an author and add it to an instance_y in the request
    """
    description = get_instance_from_string(request.POST.get("instance_y"))

    # For the author first get or create a Person
    person, created = Person.objects.get_or_create(name=request.POST.get("person"))
    author = Author(
        person=person,
        description=description,
        position=int(request.POST.get("position")),
    )
    author.save()

    return JsonResponse({"status": True})


def render_references(html_doc, short_dict):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_doc, 'html.parser')
    for tag in soup.find_all('reference-tag'):
        try: #might not have a bibtex
            ref = short_dict[int(tag.get('id'))]
            ref = ref.replace("(","").replace(")","")
            tag.string.replace_with(str(ref))
        except KeyError:
            pass
    # image suptitles are also only present in the placeholder
    for img in soup.find_all("div", class_="image-tool__caption"):
        img.string = img.get("data-placeholder")
        img["class"]="image-tool__caption cdx-input"
        
    return str(soup)


def render_description(request, pk, tostring=False):
    from main.tools.references import write_bibliography
    from pyeditorjs import EditorJsParser

    origin = request.GET.get("origin", None)
    description = Description.objects.get(pk=int(pk))
    # get all the references with bibtex 
    references = description.ref.filter(bibtex__isnull=False).exclude(bibtex__exact="")
    remaining_references = description.ref.exclude(id__in=references.values_list('id', flat=True))
    reference_items, short_dict = write_bibliography(references)

    #Render the html in backend instead of frontend, required for pdf-export
    try:
        editor_js_data = json.loads(description.content)
        parser = EditorJsParser(editor_js_data)
        html = parser.html(sanitize=False)

        #replace the reference-tags and do some manual cleanup, because this is not done by the HTMLParser 
        html2 = render_references(html, short_dict)

    except TypeError: # description.content == null
        html2 = ""
        pass

    header="Description"
    #for printing, print the site
    if description.content_object:
        header=description.content_object

    context = {
        "description": description,
        "rendered_description": html2,
        "model": "site",
        "header": header,
        "origin": origin,
        "object": description,
        "reference_items": reference_items,
        "remaining_references":remaining_references
    }

    if tostring:
        # this is for printing only
        from django.template.loader import render_to_string
        context.update({"print":True})
        return render_to_string("main/description/description_render.html", context)

    return render(request, "main/description/description_render.html", context)


urlpatterns = [
    path("edit/<int:pk>", DescriptionUpdateView.as_view(), name="main_descr_update"),
    path("add-author", create_and_add_author, name="main_description_author_add"),
    path("save", save_description, name="ajax_description_save"),
    path("get-content", get_description_content, name="ajax_description_get"),
    path(
        "render_description/<int:pk>",
        render_description,
        name="main_render_description",
    ),
    path("print-html/<int:pk>", print_html, name="main_description_print")
]
