from iosacal import R
import json
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import path
from django.db.models import Q
from main.models import models, Date, Site
from main.tools.generic import remove_x_from_y_m2m, delete_x, get_instance_from_string
from main.ajax import get_modal
from django.contrib.auth.decorators import (
    login_required,
)  # this is for now, make smarter later
from django.db.models import ProtectedError
from django.contrib import messages


def recalculate_mean(dateable):
    infinite, upper, lower = dateable.get_upper_and_lower(calculate_mean=True)
    dateable.mean_upper = upper
    dateable.mean_lower = lower
    dateable.save()
    if dateable.model == "layer":
        # recalculate the culture range (see below)
        if dateable.culture:
            dateable.culture.save()


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
    date.sigma = "95%"
    date.save()
    return JsonResponse({"status": True})


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

    # check the sigma/CI values
    wrong_ci = [
        str(x) for x in df["Sigma/CI"] if x == x and str(x)[-1] not in ["s", "σ", "%"]
    ]
    if len(wrong_ci) > 0:
        issues.append(
            f"Invalud Sigma/CI: {','.join(wrong_ci)}. Must end with 's','σ' or '%'"
        )
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
        ref_old = None

        if "Lab Code" in dat:
            try:
                # get an already existing date
                tmp = Date.objects.get(oxa=dat["Lab Code"])
                ref_old = tmp.ref.first()
            except:
                # continue with the new one
                tmp.oxa = dat["Lab Code"]
        
        # if it is a new date OR the reference is the same (then --> update)
        if "Reference" in dat:
            ref_new = Reference.objects.get(pk=dat["Reference"]["id"])

        if not tmp.pk or ref_old == ref_new:
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
            if "Sigma/CI" in dat:
                tmp.sigma = dat["Sigma/CI"]
            tmp.save()
            tmp.refresh_from_db()

            if "Curve" in dat:
                curve = dat["Curve"]
                # TODO: do something with the curve.
                # TODO: this is not working yet!

        if "Reference" in dat and not ref_old:
            tmp.ref.add(ref_new)

        tmp_layer = Layer.objects.filter(Q(site=site) & Q(name=dat["Layer"])).first()
        tmp_layer.date.add(tmp)
        tmp_layer.save()
    return JsonResponse({"status": True})


@login_required
def add(request):
    from main.forms import DateForm
    from main.models import DatingMethod, Date

    # get the layer/object the date needs to be added to
    object = get_instance_from_string(request.POST.get("object"))

    # first see if there was a simple add
    if pk := request.POST.get("date", False):
        obj = Date.objects.get(pk=int(pk))
        object.date.add(obj)
        object.save()

    else:
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
    messages.add_message(
        request,
        messages.SUCCESS,
        f"Date added to {object.model}",
    )

    request.GET._mutable = True
    request.GET.update({"object": f"{object.model}_{object.pk}", "type": "dates"})

    from main.ajax import get_modal

    return get_modal(request)


@login_required
def delete(request):
    date = get_instance_from_string(request.POST.get("instance_x"))
    object = get_instance_from_string(request.POST.get("instance_y"))

    error = None
    if date.is_used_as_limit():
        messages.add_message(
            request,
            messages.ERROR,
            "Cannot delete date that is fixed as upper or lower bound",
        )
    else:
        status, date, object = remove_x_from_y_m2m(request, "date", response=False)
        # If dates are not linked to any model, remove
        if len(date.layer_model.all()) == 0 and len(date.sample_model.all()) == 0:
            deleted = delete_x(request, response=False)

    request.GET._mutable = True
    request.GET.update({"object": f"{object.model}_{object.pk}", "type": "dates_list"})

    from main.ajax import get_modal

    return get_modal(request)


@login_required
def toggle_use(request):
    date = get_instance_from_string(request.POST.get("instance_x"))
    object = get_instance_from_string(request.POST.get("object"))
    date.hidden = date.hidden == False
    date.save(update_fields=["hidden"])

    # finally, return the modal
    request.GET._mutable = True
    request.GET.update({"object": f"{object.model}_{object.pk}", "type": "dates_list"})

    from main.ajax import get_modal

    return get_modal(request)


@login_required
def dateable_setbounds(request):
    object = get_instance_from_string(request.POST.get("instance_x"))
    try:
        object.set_upper = int(request.POST.get("upper"))
    except ValueError:
        object.set_upper = None
    try:
        object.set_lower = int(request.POST.get("lower"))
    except ValueError:
        object.set_lower = None
    object.save()
    recalculate_mean(object)

    request.GET._mutable = True
    request.GET.update({"object": f"{object.model}_{object.pk}", "type": "dates_list"})

    return get_modal(request)


@login_required
def dateable_setdate(request):
    from main.models import Date

    ## RULES ##
    # 1. If both upper and lower dates are set
    # - upper can be infinite
    # - lower cant be infinite
    #
    # 2. If only one date is set
    # - only upper and infinite --> has no meaning, so dont allow
    # - only upper --> Younger than that
    # - only lower --> Older than that (so lower can also be infinite in this case)

    object = get_instance_from_string(request.POST.get("instance_x"))

    try:
        date_upper = Date.objects.get(pk=int(request.POST.get("upper_date")))
    except ValueError:
        date_upper = None

    try:
        date_lower = Date.objects.get(pk=int(request.POST.get("lower_date")))
    except ValueError:
        date_lower = None

    # now check for the rules
    errors = False
    if date_upper and date_lower:
        if date_lower.get_upper().startswith(">"):
            messages.add_message(
                request,
                messages.ERROR,
                f"No infinite Date ({date_lower}) allowed as lower date, if upper date exists",
            )
            errors = True
    elif date_upper and not date_lower and date_upper.get_upper().startswith(">"):
        messages.add_message(
            request,
            messages.ERROR,
            f"No infinite Date ({date_upper}) allowed as only upper date. Younger than infinite is not meaningful",
        )
        errors = True

    if not errors:
        object.date_upper = date_upper
        object.date_lower = date_lower
        object.save()
        recalculate_mean(object)

    request.GET._mutable = True
    request.GET.update(
        {
            "object": f"{object.model}_{object.pk}",
            "type": "dates_list",
        }
    )

    return get_modal(request)


urlpatterns = [
    path("add", add, name="ajax_date_add"),
    path("delete", delete, name="ajax_date_unlink"),
    path("upload", batch_upload, name="ajax_date_batch_upload"),
    path("save-batch", save_verified_batchdata, name="ajax_save_verified_batchdata"),
    path("toggle_use", toggle_use, name="ajax_date_toggle"),
    path("recalibrate", recalibrate_c14, name="ajax_date_recalibrate"),
    path("set-bounds", dateable_setbounds, name="main_dateable_setbounds"),
    path("set-date", dateable_setdate, name="main_dateable_setdate"),
]
