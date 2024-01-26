from iosacal import R
import json
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import path
from django.db.models import Q
from main.models import models, Date, Site
from main.tools.generic import remove_x_from_y_m2m, delete_x, get_instance_from_string
from django.contrib.auth.decorators import (
    login_required,
)  # this is for now, make smarter later


def calibrate(estimate, plusminus, curve="intcal20"):
    curve = curve
    r = R(int(estimate), int(plusminus), "tmp")
    try:
        calibrated = r.calibrate(curve)
        raw = list(
            [(x[0], round(x[1], 4)) for x in calibrated]
        )  # list of datapoints [date, proportion]
        lower, upper = calibrated.quantiles()[95]
        return raw, upper, lower, curve
    except ValueError:
        return None, None, None, curve


@login_required
def recalibrate_c14(request):
    date = get_instance_from_string(request.POST.get("instance_x"))
    curve = request.POST.get("curve")
    raw, upper, lower, curve = calibrate(date.estimate, date.plusminus, curve=curve)
    date.upper = upper
    date.lower = lower
    date.curve = curve
    date.raw = json.dumps(raw)
    date.save()
    return JsonResponse({"status": True})


@login_required
def calibrate_c14(request):
    date = request.GET.get("estimate", False)
    pm = request.GET.get("pm", False)
    if date and pm and pm != "0":
        raw, upper, lower, curve = calibrate(date, pm)
        return JsonResponse(
            {"status": True, "lower": lower, "upper": upper, "curve": curve}
        )
    return JsonResponse({"status": False})


@login_required
def batch_upload(request):
    # handle the csv upload --> #TODO: make a verification!
    # render into new modal, so that people can verify
    # dont save anything yet, but process how it will be saved! show the table
    # TODO: maybe make a general upload-helper function, independant of the model!
    # TODO: verify required columns

    import pandas as pd
    import main.tools as tools
    from main.models import Date, Reference, Layer

    expected = Date.table_columns()
    # import csv without saving

    df = pd.read_csv(request.FILES["file"], sep=",")
    df.drop_duplicates(inplace=True)

    site = Site.objects.get(pk=int(request.GET.get("site")))
    all_layers = [x.name for x in site.layer.all()]

    # filter for expected/unexpected columns
    issues = []
    if dropped := [x for x in df.columns if x not in expected]:
        issues.append(f"Dropped Table Columns: {','.join(dropped)}")
    df = df[[x for x in df.columns if x in expected]]

    # hardcode the testing for now
    if "Reference" in df.columns:
        df["Reference"] = df.Reference.apply(lambda x: tools.references.find(x))
        if "Not Found" in set(df["Reference"]):
            issues.append("Reference was not found (see Table)")

    layer_wrong = df[df.Layer.isin(all_layers) == False].copy()
    if len(layer_wrong) > 0:
        issues.append(
            f"Removed non-existing Layers: {','.join(set(layer_wrong['Layer']))}"
        )
        df.drop(layer_wrong.index, inplace=True)
    return render(
        request,
        "main/dating/dating-batch-confirm.html",
        {
            "dataframe": df.fillna("").to_html(
                index=False, classes="table table-striped col-12"
            ),
            "issues": issues,
            "json": df.to_json(),
            "site": site,
        },
    )


@login_required
def save_verified_batchdata(request):
    import pandas as pd
    from main.models import Date, Site, Layer, Reference

    df = pd.read_json(request.POST.get("batch-data"))
    site = Site.objects.get(pk=int(request.POST.get("site")))
    df.convert_dtypes()
    # TODO: use a date-form to create instances for each row
    for i, dat in df.iterrows():
        dat = dat.dropna()
        tmp = Date(method=dat["Method"])
        if "Lab Code" in dat:
            try:
                # get an already existing date
                tmp = Date.objects.get(oxa=dat["Lab Code"])
            except:
                # continue with the new one
                tmp.oxa = dat["Lab Code"]
        # if a new date
        if not tmp.pk:
            if "Date" in dat:
                tmp.estimate = dat["Date"]
            if "Error" in dat:
                tmp.plusminus = dat["Error"]
            if "Upper Bound" in dat:
                tmp.upper = dat["Upper Bound"]
            if "Lower Bound" in dat:
                tmp.lower = dat["Lower Bound"]
            if "Notes" in dat:
                tmp.description = dat["Notes"]
            tmp.save()
            tmp.refresh_from_db()
            if "Curve" in dat:
                curve = dat["Curve"]
                # TODO: do something with the curve.
                # TODO: this is not working yet!

        if "Reference" in dat:
            tmp.ref.add(Reference.objects.get(pk=dat["Reference"]["id"]))
        tmp_layer = Layer.objects.filter(Q(site=site) & Q(name=dat["Layer"])).first()
        tmp_layer.date.add(tmp)
        tmp_layer.save()
    return JsonResponse({"status": True})


@login_required
def add(request):
    from main.forms import DateForm
    from main.models import DatingMethod, Date

    # get the layer the date needs to be added to
    object = get_instance_from_string(request.POST.get("object"))

    form = DateForm(request.POST)
    if form.is_valid():  # is always valid because nothing is required
        # create a tmp-date, dont save
        obj = Date(method="tmp")
        # check if we have the date already in the database
        # replace the tmp-date
        if oxa := form.cleaned_data.get("oxa"):
            try:
                obj = Date.objects.get(oxa=oxa)
            except Date.DoesNotExist:
                pass
        # Check of obj is now a real entry
        if not obj.pk:
            if any(
                [
                    form.cleaned_data.get(x, False)
                    for x in ["estimate", "upper", "lower"]
                ]
            ):
                obj = (
                    form.save()
                )  # post_safe signal fires here to calibrate if not done yet
                obj.refresh_from_db()
            else:
                form.add_error(None, "Please provide a Date")
        # if we _now_ have a real date entry, add to associated model (e.g. Layer)
        if obj.pk:
            object.date.add(obj)
            object.save()  # not needed for adding, but for post-save signal in layer

    # finally, return the modal
    request.GET._mutable = True
    request.GET.update({"object": f"layer_{object.pk}", "type": "dates"})

    from main.ajax import get_modal

    return get_modal(request)


@login_required
def delete(request):
    status, date, layer = remove_x_from_y_m2m(request, "date", response=False)
    # If dates are not linked to any model, remove
    if len(date.model.all()) == 0:
        return delete_x(request)
    return JsonResponse({"status": True})


@login_required
def toggle_use(request):
    date = get_instance_from_string(request.POST.get("instance_x"))
    date.hidden = date.hidden == False
    date.save(update_fields=["hidden"])
    return JsonResponse({"status": True})


urlpatterns = [
    path("add", add, name="ajax_date_add"),
    path("delete", delete, name="ajax_date_unlink"),
    path("upload", batch_upload, name="ajax_date_batch_upload"),
    path("save-batch", save_verified_batchdata, name="ajax_save_verified_batchdata"),
    path("calibrate", calibrate_c14, name="ajax_date_cal"),
    path("toggle_use", toggle_use, name="ajax_date_toggle"),
    path("recalibrate", recalibrate_c14, name="ajax_date_recalibrate"),
]
