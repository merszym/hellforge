from main.models import models
from main.models import AnalyzedSample, Sample, Project, SampleBatch, Site
from django.http import JsonResponse, HttpResponse
from django.urls import path
from django import forms
from django.shortcuts import render
import main.tools as tools
from django.db.models import Q
import pandas as pd
import json
from django.contrib.auth.decorators import (
    login_required,
)  # this is for now, make smarter later
from django.contrib import messages


## DNA content
## At the moment only quicksand content...
def get_site_dna_content(request, pk):
    
    site = Site.objects.get(pk=int(pk))
    context = {"object": site}
   
    return render(request, "main/site/site-dna-content.html", context)


def unset_library_filters(request):
    request.session.pop('filter_batch_pk','')
    request.session.pop('filter_probe','')
    request.session.pop('filter_sample_pk','')
    request.session.pop('filter_controls','')


def set_sample_cookie(request, pk):
    sample = Sample.objects.get(pk=pk)
    # unset library-filters
    unset_library_filters(request)

    #only filter by sample
    request.session['filter_sample_pk'] = sample.pk

    return get_libraries(request, sample.site.pk, unset=False)


def filter_libraries(request, query):
    if not request.user.is_authenticated:
        from main.tools.projects import get_project
        project = get_project(request)
        query = query.filter(project=project)
    if 'filter_batch_pk' in request.session:
        batch = tools.generic.get_instance_from_string(f"samplebatch_{request.session['filter_batch_pk']}")
        query = query.filter(
            Q(sample__batch=batch) 
        )
    if 'filter_probe' in request.session:
        probe = request.session['filter_probe']
        query = query.filter(
            Q(probes=probe) 
        )
    if 'filter_sample_pk' in request.session:
        # if this is the case, then only this cookie is set for the library filters!
        sample = tools.generic.get_instance_from_string(f"sample_{request.session['filter_sample_pk']}")
        query = query.filter(
            Q(sample=sample) 
        )
    return query

def get_libraries(request, pk, unset=True, return_query=False):
    """
    from one site, get all the (filtered) samples and display the list of libraries
    """
    object = Site.objects.get(pk=pk)
    samples = tools.samplebatch.filter_samples(request, Sample.objects.filter(site=object))

    if request.method == 'POST':
        if unset:
            unset_library_filters(request)
        # we want to filter the libraries, so set the cookies for the filter
        batch = request.POST.get("batch", "all")
        probe = request.POST.get("probe", "all")
        filter_controls = "on" == request.POST.get("filter_controls", "")

        if batch != 'all':
            batch = tools.generic.get_instance_from_string(batch)
            request.session['filter_batch_pk'] = batch.pk
            request.session['filter_batch_name'] = batch.name
        
        if probe != 'all':
            request.session['filter_probe'] = probe
        
        if unset:
            request.session['filter_controls'] = filter_controls

    query = filter_libraries(request, AnalyzedSample.objects.filter(sample__in=samples))
    try:
        if not request.session['filter_controls']:
            query = update_query_for_negatives(query)
    except KeyError:
        query = update_query_for_negatives(query)

    if return_query:
        return query

    return render(request, 'main/analyzed_samples/analyzedsample_table.html', {'object_list':query, 'site':object})


def update_query_for_negatives(query, project=False):
    lnc_negatives = set(query.values_list("lnc_batch","probes"))
    all_plates = [x[0] for x in lnc_negatives]
    enc_negatives = set(query.values_list("enc_batch","probes"))
    lnc_ids = []
    enc_ids = []

    if project:
        pre_select = AnalyzedSample.objects.filter(project=project)
    else:
        pre_select = AnalyzedSample.objects.all()
    
    for batch, probe in lnc_negatives:
        lnc_query = pre_select.filter(
            Q(sample__isnull=True) & Q(lnc_batch=batch) & Q(tags="LNC") & Q(probes=probe)
        )
        lnc_ids.extend(list(lnc_query.values_list("pk", flat=True)))

    for batch, probe in enc_negatives:
        # try to fetch only the ones on the same library plate
        enc_query = pre_select.filter(
            Q(sample__isnull=True) & Q(enc_batch=batch) & Q(tags="ENC") & Q(probes=probe) & Q(lnc_batch__in=all_plates)
        )
        # if non exist - fetch from other plates as well
        if len(enc_query)==0:
            enc_query = pre_select.filter(
                Q(sample__isnull=True) & Q(enc_batch=batch) & Q(tags="ENC") & Q(probes=probe)
            )

        enc_ids.extend(list(enc_query.values_list("pk", flat=True)))

    # got the ENC and LNC entries, now update the analyzedsamples query again to include LNC and ENC

    updated_query = AnalyzedSample.objects.filter(
        Q(pk__in=query.values_list("pk", flat=True))
        | Q(pk__in=lnc_ids)
        | Q(pk__in=enc_ids)
    )

    return updated_query


class AnalyzedSampleForm(forms.ModelForm):
    class Meta:
        model = AnalyzedSample
        fields = ["seqrun", "seqpool", "lane"]


def handle_library_file(request, file):
    df = pd.read_csv(file, sep=",")
    df.drop_duplicates(inplace=True)

    # filter for expected/unexpected columns
    expected = AnalyzedSample.table_columns()
    issues = []
    if dropped := [x for x in df.columns if x not in expected]:
        issues.append(f"Dropped Table Columns: {','.join(dropped)}")
    df = df[[x for x in df.columns if x in expected]]

    # check if sample parents exist
    samples = Sample.objects.values("name")

    if dropped := [
        x for x in df["Sample Name"] if len(samples.filter(name=x)) == 0
    ]:
        dropped = [
            x for x in dropped if x == x
        ]  # ignore empty samples, as they are negative controls
        if len(dropped) > 0:
            issues.append(f"Samples not in Database: {','.join(dropped)}")
    df = df[df["Sample Name"].isin(dropped) == False]

    print(Sample.objects.get(name=set(df['Sample Name']).pop()))

    return render(
        request,
        "main/modals/sample_modal.html",
        {
            "type": "libraries_confirm",
            "object":samples.first(),
            "dataframe": df.fillna("").to_html(
                index=False, classes="table table-striped col-12"
            ),
            "issues": issues,
            "json": df.to_json(),
        },
    )


def save_verified(request):
    df = pd.read_json(request.POST.get("batch-data"))
    df.convert_dtypes()

    batch = SampleBatch.objects.get(pk=int(request.GET.get("batch")))
    project = Project.objects.get(namespace=request.session["session_project"])

    def value_or_none(val):
        if val == "nan" or val != val:
            return None
        return val

    # go through the layers
    for i, row in df.iterrows():
        if row["Tag"] in ["LNC", "ENC"]:
            sample = None
        else:
            sample = Sample.objects.get(name=row["Sample Name"])
        # try if the library already exists
        object, created = AnalyzedSample.objects.get_or_create(
            library=row["Library"],
            seqrun=row["Sequencing Run"],
            lane=row["Sequencing Lane"],
        )
        # set or update
        object.sample = sample
        object.lysate = value_or_none(row["Lysate"])
        object.capture = value_or_none(row["Capture"])
        object.probes = value_or_none(row["Capture Probe"])
        object.enc_batch = value_or_none(row["ENC Batch"])
        object.lnc_batch = value_or_none(row["LNC Batch"])
        object.molecules_qpcr = value_or_none(row["Molecules (qPCR)"])
        object.efficiency = value_or_none(row["Efficiency"])
        object.tags = value_or_none(row["Tag"])
        object.seqpool = value_or_none(row["Sequencing Pool"])
        object.lane = value_or_none(row["Sequencing Lane"])        
        object.save()
    from main.tools.site import get_site_samplebatch_tab

    return get_site_samplebatch_tab(request, batch.pk)


def tags_update(request, pk):
    object = AnalyzedSample.objects.get(pk=pk)
    val = request.POST.get("tags", None)

    object.tags = val
    object.save()

    # finally, return the modal
    messages.add_message(
        request,
        messages.SUCCESS,
        f"Update of tag successful",
    )

    request.GET._mutable = True
    request.GET.update({"object": f"{object.model}_{object.pk}", "type": "tags"})

    from main.ajax import get_modal

    return get_modal(request)


def seqrun_update(request, pk):
    object = AnalyzedSample.objects.get(pk=pk)
    # in case we want to update all
    old_run = object.seqrun
    old_lane = object.lane
    old_pool = object.seqpool

    form = AnalyzedSampleForm(request.POST, instance=object)

    if form.is_valid():
        form.save()

    if request.GET.get("all", "no") == "yes":
        libs = AnalyzedSample.objects.filter(
            Q(seqrun=old_run)
            & Q(seqpool=old_pool)
            & Q(lane=old_lane)
            & Q(sample__site=object.sample.site)
        )
        for lib in libs:
            form = AnalyzedSampleForm(request.POST, instance=lib)
            if form.is_valid():
                form.save()

    # finally, return the modal
    messages.add_message(
        request,
        messages.SUCCESS,
        f"Update of Seqrun(s) successful",
    )

    request.GET._mutable = True
    request.GET.update({"object": f"{object.model}_{object.pk}", "type": "edit_seqrun"})

    from main.ajax import get_modal

    return get_modal(request)


def qc_toggle(request, pk):
    object = AnalyzedSample.objects.get(pk=pk)

    object.qc_pass = object.qc_pass == False
    object.save()

    if object.qc_pass:  # needs to get removed
        return HttpResponse("<span style='color:green; cursor:pointer;'>Pass</span>")
    else:
        return HttpResponse("<span style='color:red; cursor:pointer;'>Fail</span>")


urlpatterns = [
    path("save", save_verified, name="ajax_save_verified_analyzedsamples"),
    path("<int:pk>/update-tags", tags_update, name="main_analyzedsample_tagupdate"),
    path(
        "<int:pk>/update-seqrun", seqrun_update, name="main_analyzedsample_seqrunupdate"
    ),
    path("<int:pk>/update-qc", qc_toggle, name="main_analyzedsample_qctoggle"),
    path("get-data/<int:pk>", get_libraries, name="main_analyzedsample_getdata"),
    path("set-sample-filter/<int:pk>", set_sample_cookie, name='main_analyzedsample_setfilter'),    
    path("dna/<int:pk>", get_site_dna_content, name="main_site_dna_tab"),

]
