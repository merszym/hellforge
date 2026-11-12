from main.tools.generic import add_x_to_y_m2m, delete_x, get_instance_from_string
from main.models import Synonym, Site, SampleBatch
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from django.urls import path
import copy


def create_and_add(request):
    """
    create a synonym and add it to the object in the request
    """
    object = get_instance_from_string(request.POST.get("object"))

    name = request.POST.get("name")
    type = request.POST.get("type")

    synonym = Synonym(name=name, type=type)
    synonym.save()
    synonym.refresh_from_db()

    object.synonyms.add(synonym)

    # now return the right modal
    request.GET._mutable = True

    if object.model == "layer":
        type = "edit"
    elif object.model == "sample":
        type = "edit_synonyms"

    request.GET.update({"object": f"{object.model}_{object.pk}", "type": type})

    from main.ajax import get_modal

    return get_modal(request)


def sample_synonyms(scope, site=None, batch=None):
    """
    the synonyms of samples (each sample has its own synonym-entries) in the scope: batch, site or all
    """
    synonyms = Synonym.objects.filter(sample__isnull=False)
    if scope == "batch":
        synonyms = synonyms.filter(sample__batch=batch)
    elif scope == "site":
        synonyms = synonyms.filter(sample__site=site)
    return synonyms


@login_required
def rename_type(request):
    """
    rename a synonym-type of the samples (the columns of the sample-table), in the batch, the site or everywhere.
    renaming to an existing type merges the two columns
    """
    site = Site.objects.get(pk=request.GET.get("site"))
    batch = SampleBatch.objects.filter(pk=request.GET.get("batch") or None).first()
    context = {"site": site, "batch": batch, "selected": request.GET.get("type", "")}

    if request.method == "POST":
        old, new = request.POST.get("old", ""), request.POST.get("new", "").strip()
        scope = request.POST.get("scope", "site")
        context["selected"] = old
        if not new:
            context["error"] = "The new name is empty"
        elif new == old:
            context["error"] = "The new name is the same as the old one"
        else:
            synonyms = sample_synonyms(scope, site, batch).filter(type=old)
            # clashes: samples that have a synonym of the new type already
            clashes = (
                Synonym.objects.filter(type=new, sample__in=synonyms.values("sample"))
                .values("sample", "sample__name", "name")
                .order_by("sample__name")
            )
            clash = request.POST.get("clash", "")  # how to handle the clashes: skip the samples or rename anyway
            if clashes and clash == "skip":
                synonyms = synonyms.exclude(sample__in=[entry["sample"] for entry in clashes])
            if clashes and clash not in ["skip", "rename"]:
                old_names = dict(synonyms.values_list("sample", "name"))
                context.update({
                    "clashes": [dict(entry, old_name=old_names.get(entry["sample"])) for entry in clashes],
                    "old": old, "new": new, "scope": scope,
                })
            else:
                ids = list(synonyms.values_list("pk", flat=True))
                context["renamed"] = Synonym.objects.filter(pk__in=ids).update(type=new)
                context.update({"old": old, "new": new, "selected": new, "skipped": len(clashes) if clash == "skip" else 0})

    # all types of sample-synonyms, with the number of synonyms in the batch, the site and in total
    context["types"] = (
        Synonym.objects.filter(sample__isnull=False)
        .values("type")
        .annotate(
            total=Count("pk", distinct=True),
            at_site=Count("pk", filter=Q(sample__site=site), distinct=True),
            in_batch=Count("pk", filter=Q(sample__batch=batch), distinct=True) if batch else Count(None),
        )
        .order_by("type")
    )
    return render(request, "main/synonyms/rename-type-modal.html", context)


urlpatterns = [
    path("add", create_and_add, name="main_synonym_add"),
    path("delete", delete_x, name="main_synonym_delete"),
    path("rename-type", rename_type, name="main_synonym_rename_type"),
]
