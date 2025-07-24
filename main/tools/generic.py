from main.models import models, Project
from main.queries import get_queryset
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse, FileResponse
from django.urls import path, reverse
from django.shortcuts import render
from django.contrib.auth.decorators import (
    login_required,
)  # this is for now, make smarter later
from datetime import datetime
import json, re
import pandas as pd
import numpy as np
import csv

from main.tools.analyzed_samples import update_query_for_negatives


def return_next(request, next, object="instance_x"):
    # return html if the request came from a modal...
    _, type = next.split("_", 1)

    request.GET._mutable = True
    request.GET.update({"object": request.POST.get(object), "type": type})

    from main.ajax import get_modal

    return get_modal(request)

# data download from dataframe
class Echo:
    """An object that implements just the write method of a json row-object."""
    def write(self, value):
        return value

def json_to_csv_rows(data, columns=[]):
    """
    Generator to yield CSV rows from JSON data.
    Assumes 'data' is a generator of dictionaries.
    BUT it sometimes also is a list of dictionaries...
    """
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)

    # Extract headers from the first JSON object
    if not data:
        return  # No data to process
    
    if len(columns) == 0:
        header = False
    else:
        yield writer.writerow(columns)
        header = True

    # Write each row
    for row in data:
        # in case the row is a list of entries
        if not header:
            columns = list(row.keys())
            yield writer.writerow(columns)
            header = True
        yield writer.writerow([row.get(col, "") for col in columns])

def download_csv(data, name="download.csv", columns=[]):

    today = datetime.strftime(datetime.today(), "%Y%m%d")

    return StreamingHttpResponse(
        json_to_csv_rows(data, columns=columns),
        content_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={today}_{name}"},
    )

def get_dataset_df(qs, start, **kwargs):
    # iterate over the objects, collect data, as specified in the models
    # do it as a generator to allow streaming
    for entry in qs:
        if start.model == 'project':
            data = start.get_data()
        else:
            data= {}
        entry_data = entry.get_data(**kwargs)
        # this could now be more than one row,so check if its a list
        if isinstance(entry_data, list):
            for subdata in data:
                tmp = data.copy()
                tmp.update(subdata)
                yield tmp
        # else return a single row as dict
        data.update(entry_data)
        yield data

def get_dataset(request):
    """
    Download a Dataset
    GET request:
    ?start --> site, project
    ?unique --> which parameter is the unique (m:1) column (analyzedsample, sample)
    
    I will specify for each Model separately, what to include in the output table
    """
    start = get_instance_from_string(request.GET.get("from"))
    unique = request.GET.get("unique")
    
    # First, get the project
    if namespace := request.session.get("session_project", False):
        project = Project.objects.get(namespace=namespace)
    else:
        project = None

    qs = get_queryset(start, unique, authenticated=request.user.is_authenticated, project=project)

    # filter for either in the right project OR user is authenticated!

    # and get the generator that yields single rows for download stream
    data = get_dataset_df(qs, start, project=project)

    # download the data
    return download_csv(data, name=f"{start}_{unique}_m_1.csv")


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
    field = request.POST.get('field',False)
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
