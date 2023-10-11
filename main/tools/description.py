from main.models import Person, Author, Description, Reference
from main.tools.generic import get_instance_from_string, delete_x
from django.http import JsonResponse
from django.urls import path
from django.views.generic import UpdateView
from django.views.decorators.csrf import csrf_exempt
import json
from django.urls import reverse
from django.contrib.auth.decorators import login_required  # this is for now, make smarter later
from django.contrib.auth.mixins import LoginRequiredMixin  # this is for now, make smarter later
from main.tools.generic import get_instance_from_string
from django.shortcuts import render


# Get description json for detail views in editor.js
def get_description_content(request):
    description = Description.objects.get(pk=int(request.GET.get("id")))
    return JsonResponse(
        json.loads(description.content) if description.content else {"empty": True, "model": request.GET.get("model")}
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

    goto = {"site": "site_detail", "project": "main_project_detail", "culture": "culture_detail"}
    model_kwargs = {
        "site": {"pk": description.content_object.id},
        "culture": {"pk": description.content_object.id},
        "project": {"namespace": getattr(description.content_object, "namespace", None)},
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
    author = Author(person=person, description=description, position=int(request.POST.get("position")))
    author.save()

    return JsonResponse({"status": True})


def render_description(request, pk):
    origin = request.GET.get("origin", None)
    description = Description.objects.get(pk=int(pk))
    return render(
        request,
        "main/description/description_render.html",
        {"description": description, "model": "site", "origin": origin, "object": description},
    )


urlpatterns = [
    path("edit/<int:pk>", DescriptionUpdateView.as_view(), name="main_descr_update"),
    path("add-author", create_and_add_author, name="main_description_author_add"),
    path("save", save_description, name="ajax_description_save"),
    path("get-content", get_description_content, name="ajax_description_get"),
    path("render_description/<int:pk>", render_description, name="main_render_description"),
]
