from django.views.generic import CreateView, UpdateView, ListView
from django.shortcuts import render
from django.urls import path
from main.models import Person, Affiliation
from django.http import JsonResponse
import copy
from main.tools.generic import (
    add_x_to_y_m2m,
    remove_x_from_y_m2m,
    get_instance_from_string,
    delete_x,
)
from django.contrib.auth.decorators import (
    login_required,
)  # this is for now, make smarter later
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)  # this is for now, make smarter later


class PersonListView(LoginRequiredMixin, ListView):
    model = Person
    template_name = "main/contact/person_list.html"

    def get_context_data(self, **kwargs):
        context = super(PersonListView, self).get_context_data(**kwargs)
        extra_context = {
            "available_affiliations": [x.name for x in Affiliation.objects.all()]
        }
        context.update(extra_context)
        return context


@login_required
def create_from_string(request):
    """Create a new Person from String. Add additional information later"""
    person = Person(name=request.POST.get("person_search").strip(), email="placeholder@fill.me")
    person.save()
    person.refresh_from_db()
    return JsonResponse({"status": True, "pk": person.pk})


@login_required
def create_and_add_affiliation(request):
    """
    get or create an affiliation and link it to a Person via a junction
    
    """
    person = get_instance_from_string(request.POST.get("instance_x"))
    position = int(request.POST.get('position'))
    
    affiliation, created = Affiliation.objects.get_or_create(
        name=request.POST.get("affiliation").strip()
    )


    from main.models import AffiliationPersonJunction

    AffiliationPersonJunction(person=person, affiliation=affiliation, position=position).save()

    ## return the updated form
    return render(request, 'main/contact/person_form.html', {'person':person, 'display':True})


@login_required
def remove_affiliation(request):
    """
    remove an affiliation from the person
    """
    return remove_x_from_y_m2m(request, "affiliation")


@login_required
def update_person(request):
    person = get_instance_from_string(request.POST.get("instance_x"))
    person.name = request.POST.get("name")
    person.email = request.POST.get("email")
    person.orcid = request.POST.get("orcid_id")
    person.save()
    return JsonResponse({"status": True})


urlpatterns = [
    path("list", PersonListView.as_view(), name="main_person_list"),
    path("create", create_from_string, name="main_person_create"),
    path(
        "affiliation_add",
        create_and_add_affiliation,
        name="main_contact_affiliation_add",
    ),
    path(
        "affiliation_remove", remove_affiliation, name="main_contact_affiliation_remove"
    ),
    path("update", update_person, name="main_person_update"),
]
