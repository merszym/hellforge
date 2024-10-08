from main.models import models, Sample
from main.queries import queries, get_querysets
from django.http import JsonResponse, HttpResponse
from django.urls import path, reverse
from django.shortcuts import render
from django.contrib.auth.decorators import (
    login_required,
)  # this is for now, make smarter later
from datetime import datetime
import json
import pandas as pd
import numpy as np

from main.tools.analyzed_samples import update_query_for_negatives


def return_next(request, next, object="instance_x"):
    # return html if the request came from a modal...
    _, type = next.split("_", 1)

    request.GET._mutable = True
    request.GET.update({"object": request.POST.get(object), "type": type})

    from main.ajax import get_modal

    return get_modal(request)


def get_dataset_df(qs, start, include):
    # iterate over the m:1 frame, collect information from models
    records = []
    for entry in qs:
        # start is the "1", e.g. project
        data = start.get_data()
        for incl in include:
            if incl == "null":
                continue
            # check if there are _multiple entries_ for the incl
            # these need to be squashed into one line
            # example person can be contact for multiple sites
            try:
                incl_entries = getattr(entry, incl, False).all()
                data.update(models[incl].squash_data(incl_entries))
            except AttributeError:
                # if there is a foreign-key relationship .all() fails
                # in this case, try if an entry exists
                try:
                    data.update(getattr(entry, incl, False).get_data())
                except AttributeError:
                    # if that fails, add empty lines...
                    empty = {k: None for k in models[incl].table_columns()}
                    data.update(empty)
        data.update(entry.get_data())
        records.append(data)
    df = pd.DataFrame.from_records(records)
    return df


def get_dataset(request):
    """
    Download a Dataset
    This is the API to get Data out of the Database again.

    This is not yet thought through or finished...

    GET request:
    ?start --> site, project
    ?unique --> which parameter is the unique (m:1) column (library, sample, layer?)
    ?include --> include intermediate columns (like sample information)

    specifiy at each model(!) or separate queries.py file, how the output columns look like.
    """
    # for now, only site works
    # define the starting point, its the classical model_pk syntax
    start = get_instance_from_string(request.GET.get("from"))
    column = start.model
    unique = request.GET.get("unique")
    include = request.GET.get("include", "null").split(",")
    extend = request.GET.get("extend", 0)

    # now set up the query
    filter = {queries(column, unique): start}

    if unique == "date" and column == "site":
        qs = start.get_dates()

    elif unique == "quicksand_analysis":
        qs = get_querysets(column, unique, start)

    else:
        qs = models[unique].objects.filter(**filter).distinct()

        if unique in ["analyzedsample", "library"]:
            qs = update_query_for_negatives(qs)

    # and get the dataframe
    df = get_dataset_df(qs, start, include)

    # if extend, add the entries of a lower hierarchie that are not in unique
    # e.g. all samples even if no libraries exist
    if extend:
        # now some of the entries are a subset of the first query
        # so lets filter them out
        excl = qs.values(extend)
        eqs = (
            models[extend]
            .objects.filter(**{queries(column, extend): start})
            .exclude(pk__in=excl)
        )

        # and get the dataset
        df2 = get_dataset_df(eqs, start, include)
        # in case the unique call was empty, dont filter columns
        if len(df.columns) > 0:
            df2 = df2[[x for x in df2.columns if x in df.columns]].copy()
        df = pd.concat([df, df2], ignore_index=True)

        # remove some weird error message
        for col in df.columns:
            df[col] = df[col].fillna("").apply(lambda x: str(x) if x != None else "")

        # sort the data again
        df = df.sort_values(by=list(df2.columns))

    # download the data
    return download_csv(df, name=f"{start}_{unique}_m_1.csv")


@login_required
def search(request):
    kw = request.POST.get("keyword")
    origin = request.POST.get("origin")
    model = request.POST.get("model")
    q = models[model].filter(kw)
    return render(
        request,
        f"main/{model}/{model}-searchresults.html",
        context={"object_list": q, "origin": origin},
    )


def get_instance_from_string(string):
    # Get the primary key of the model from the data
    # return the instance
    model, pk = string.split("_")
    return models[model].objects.get(pk=int(pk))


@login_required
def unset_fk(request, field=None, response=True):
    """
    set the foreign key relationship to None
    """
    x = get_instance_from_string(request.POST.get("instance_x"))
    if not field:
        field = request.POST.get("field")
    if x:
        setattr(x, field, None)
        x.save()

    # return html if the request came from a modal...
    if next := request.GET.get("next", False):
        return return_next(request, next)

    if x:
        return JsonResponse({"status": True}) if response else (True, x)
    return JsonResponse({"status": False}) if reponse else False


@login_required
def set_x_fk_to_y(request, field=None, response=True):
    """
    set the foreign key of x to y
    x = profile
    y = site
    field = profile
    --
    profile.site = site
    """
    if not field:
        field = request.POST.get("instance_y").split("_")[0]
    x = get_instance_from_string(request.POST.get("instance_x"))
    y = get_instance_from_string(request.POST.get("instance_y"))
    if x and y:
        setattr(x, field, y)
        x.save()

    # return html if the request came from a modal...
    if next := request.GET.get("next", False):
        return return_next(request, next)

    return JsonResponse({"status": True}) if response else (True, x, y)


@login_required
def add_x_to_y_m2m(request, field=None, response=True):
    x = get_instance_from_string(request.POST.get("instance_x"))
    y = get_instance_from_string(request.POST.get("instance_y"))
    if not field:
        field = request.POST.get("instance_x").split("_")[0]
    if x and y:
        getattr(y, field).add(x)

    # return html if the request came from a modal...
    if next := request.GET.get("next", False):
        return return_next(request, next, object="instance_y")

    return JsonResponse({"status": False}) if response else (True, x, y)


@login_required
def remove_x_from_y_m2m(request, field=None, response=True):
    x = get_instance_from_string(request.POST.get("instance_x"))
    y = get_instance_from_string(request.POST.get("instance_y"))
    if not field:
        field = request.POST.get("instance_x").split("_")[0]
    if x and y:
        getattr(y, field).remove(x)

    # return html if the request came from a modal...
    if next := request.GET.get("next", False):
        return return_next(request, next, object="instance_y")

    if x:
        return JsonResponse({"status": True}) if response else (True, x, y)
    return JsonResponse({"status": False}) if reponse else (False, x, y)


@login_required
def delete_x(request, response=True):
    """
    A generic function to delete an object
    """
    x = get_instance_from_string(request.POST.get("instance_x"))
    x.delete()

    # return html if the request came from a modal...
    if next := request.GET.get("next", False):
        return return_next(request, next)

    return JsonResponse({"status": True}) if response else True


# data download from dataframe
def download_csv(df, name="download.csv"):
    from django.core.files.base import ContentFile

    today = datetime.strftime(datetime.today(), "%Y%m%d")
    file_to_send = ContentFile(df.to_csv(index=False))
    response = HttpResponse(file_to_send, content_type="application/octet-stream")
    response["Content-Disposition"] = f"attachment; filename={today}_{name}"

    return response


urlpatterns = [
    path("search", search, name="main_generic_search"),
    path("rmm2m/<str:field>", remove_x_from_y_m2m, name="main_generic_rmm2m"),
    path("rmm2m", remove_x_from_y_m2m, name="main_generic_rmm2m"),
    path("unsetfk/<str:field>", unset_fk, name="main_generic_unsetfk"),
    path("unsetfk", unset_fk, name="main_generic_unsetfk"),
    path("setfk/<str:field>", set_x_fk_to_y, name="main_generic_setfk"),
    path("setfk/", set_x_fk_to_y, name="main_generic_setfk"),
    path("addm2m/<str:field>", add_x_to_y_m2m, name="main_generic_addm2m"),
    path("addm2m", add_x_to_y_m2m, name="main_generic_addm2m"),
    path("deletex", delete_x, name="main_generic_delete"),
    path("get-dataset", get_dataset, name="get_dataset"),
]
