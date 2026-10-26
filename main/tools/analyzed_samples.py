from main.models import models
from main.models import (
    AnalyzedSample,
    Sample,
    Project,
    SampleBatch,
    Site,
    ProbeTranslationTable,
    QuicksandAnalysis,
    HumanDiagnosticPositions,
    NedflowAnalysis,
)
from django.http import JsonResponse, HttpResponse
from django.urls import path
from django import forms
from django.shortcuts import render
import main.tools as tools
from django.db.models import Q, Prefetch
from collections import defaultdict
import pandas as pd
import json, io
from django.contrib.auth.decorators import (
    login_required,
)  # this is for now, make smarter later
from django.contrib import messages
from django.core.paginator import Paginator

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
    request.session.pop('filter_search','')


def set_sample_cookie(request, pk):
    sample = Sample.objects.get(pk=pk)
    # unset library-filters
    unset_library_filters(request)

    #only filter by sample
    request.session['filter_sample_pk'] = sample.pk
    request.session['filter_sample_name'] = sample.name

    return get_libraries(request, sample.site.pk, unset=False, filters_changed=True)


# the related objects needed to display the layer/culture of a library (see Sample.get_layer)
# prefix with 'analyzedsample__' for the analysis models
LIBRARY_LAYER_RELATED = [
    'sample__batch',
    'sample__layer__culture',
    'sample__layer__layer',
    'sample__sample__layer__culture',
    'sample__sample__layer__layer',
]


def probe_translations():
    """
    {probes: display-string} for the ProbeTranslationTable, to avoid one query per row
    """
    translations = defaultdict(list)
    for entry in ProbeTranslationTable.objects.all():
        translations[entry.probes].append(str(entry))
    # same as AnalyzedSample.probes_str: ambiguous translations are ignored
    return {k: v[0] for k, v in translations.items() if len(v) == 1}


# rows per page of the analysis tables (0: all rows)
PAGE_SIZES = [100, 300, 1000, 0]
DEFAULT_PAGE_SIZE = 300


def paginate_rows(request, object_list):
    """
    paginate the rows of an analysis table (quicksand etc.)
    page and per_page come from the filter-form, see main/common/pagination.html
    """
    try:
        per_page = int(request.POST.get("per_page", DEFAULT_PAGE_SIZE))
    except ValueError:
        per_page = DEFAULT_PAGE_SIZE
    paginator = Paginator(object_list, per_page or max(len(object_list), 1))
    page = paginator.get_page(request.POST.get("page", 1))
    return {
        "object_list": page,
        "page_obj": page,
        "per_page": per_page,
        "page_sizes": PAGE_SIZES,
        "default_page_size": DEFAULT_PAGE_SIZE,
    }


# the text-fields of a library that are searched by the free-text filter
LIBRARY_SEARCH_FIELDS = [
    "lysate", "enc_batch", "library", "reamp_library", "lnc_batch", "capture", "probes",
    "seqrun", "lane", "seqpool", "tags", "ena_genbank", "ena_accession",
]


def search_libraries(query, text):
    """
    keep the libraries that contain the text in any of their fields (case-insensitive)
    """
    condition = Q()
    for field in LIBRARY_SEARCH_FIELDS:
        condition |= Q(**{f"{field}__icontains": text})
    return query.filter(condition)


def filter_libraries(request, query, filter_probes=True):
    if not request.user.is_authenticated:
        from main.tools.projects import get_project

        project = get_project(request)
        query = query.filter(project=project, qc_pass=True)

    if 'filter_batch_pk' in request.session:
        batch = tools.generic.get_instance_from_string(f"samplebatch_{request.session['filter_batch_pk']}")
        query = query.filter(
            Q(sample__batch=batch) 
        )
    if filter_probes and 'filter_probe' in request.session:
        # several probes can be selected
        probes = request.session['filter_probe']
        if isinstance(probes, str):  # sessions from before the multi-select
            probes = [probes]
        query = query.filter(
            Q(probes__in=probes)
        )
    if request.session.get('filter_search'):
        query = search_libraries(query, request.session['filter_search'])
    if 'filter_sample_pk' in request.session:
        # if this is the case, then only this cookie is set for the library filters!
        sample = tools.generic.get_instance_from_string(f"sample_{request.session['filter_sample_pk']}")
        query = query.filter(
            Q(sample=sample) 
        )
    return query

def get_libraries(request, pk, unset=True, return_query=False, filters_changed=False):
    """
    from one site, get all the (filtered) samples and display the list of libraries
    """

    object = Site.objects.get(pk=pk)
    project = tools.projects.get_project(request)

    #first, do the whole shebang with the samples again!
    samples_qs = Sample.objects.filter(site=object, domain='mpi_eva') \
        .order_by('sample__name')

    samples = tools.samplebatch.filter_samples(request, samples_qs)

    if request.method == 'POST':
        if unset:
            unset_library_filters(request)
        # we want to filter the libraries, so set the cookies for the filter
        batch = request.POST.get("batch", "all")
        probes = [x for x in request.POST.getlist("probe") if x != 'all']
        sample = request.POST.get("sample","all")
        filter_controls = "on" == request.POST.get("filter_controls", "")
        search = request.POST.get("search", "").strip()

        if batch != 'all':
            batch = tools.generic.get_instance_from_string(batch)
            request.session['filter_batch_pk'] = batch.pk
            request.session['filter_batch_name'] = batch.name
        
        if probes:
            request.session['filter_probe'] = probes
        
        if sample != 'all':
            sample = tools.generic.get_instance_from_string(sample)
            request.session['filter_sample_pk'] = sample.pk
            request.session['filter_sample_name'] = sample.name
        
        if search:
            request.session['filter_search'] = search

        if unset:
            request.session['filter_controls'] = filter_controls

    analyzed_samples = AnalyzedSample.objects.filter(sample__in=samples)
   
    query = filter_libraries(request, analyzed_samples)

    try:
        if not request.session['filter_controls']:
            query = update_query_for_negatives(query, project=project, authenticated=request.user.is_authenticated)
    except KeyError:
        query = update_query_for_negatives(query, project=project, authenticated=request.user.is_authenticated)

    # load the sample/layer information in bulk instead of per row
    query = query.select_related(*LIBRARY_LAYER_RELATED)

    if return_query:
        return query

    # for the table only: the analyses are ordered, so that .first in the template uses
    # the prefetched data, and the large data-field is not needed for the display
    query = query.prefetch_related(
        'project',
        Prefetch('quicksand_analysis', queryset=QuicksandAnalysis.objects.order_by('pk').defer('data')),
        Prefetch('matthias_analysis', queryset=HumanDiagnosticPositions.objects.defer('data')),
        Prefetch('nedflow_analysis', queryset=NedflowAnalysis.objects.order_by('pk').defer('data')),
    )
    
    # for the filter-dropdowns, only pk and name are needed
    batches = SampleBatch.objects.filter(sample__in=samples_qs).distinct().order_by('name')
    # all the probes to choose from, independent of the probes that are already selected
    probes = sorted(
        filter_libraries(request, analyzed_samples, filter_probes=False)
        .exclude(probes=None)
        .order_by()
        .values_list('probes', flat=True)
        .distinct()
    )

    #paginator to improve speed
    paginator = Paginator(query, 300)
    page_number = request.POST.get("page", 1)
    page_obj = paginator.get_page(page_number)

    response = render(
        request, 
        'main/analyzed_samples/analyzedsample_table.html', 
        {
            'object_list':page_obj, 
            'site':object,
            'batches':batches,
            'probes':probes,
            'probe_names':probe_translations(),
            'total':paginator.count,
            'page':page_number
        }
    )
    # the analyses-section (quicksand etc.) listens to this event and reloads.
    # Not needed when only switching pages of the table
    if filters_changed or (request.method == 'POST' and not request.POST.get('paginate')):
        response['HX-Trigger'] = 'libraries-filtered'
    return response

def search_samples(request, pk):
    """
    search-as-you-type for the sample-filter of the library table
    """
    limit = 20
    keyword = request.GET.get("sample_search", "").strip()
    samples = tools.samplebatch.filter_samples(
        request, Sample.objects.filter(site__pk=pk, domain='mpi_eva')
    )
    if keyword:
        samples = samples.filter(name__icontains=keyword)
    samples = list(samples.order_by('name').values('pk', 'name')[:limit + 1])

    return render(
        request,
        'main/analyzed_samples/sample-searchresults.html',
        {'samples': samples[:limit], 'more': len(samples) > limit}
    )


def download_selection(request, pk):
    qs = get_libraries(request, pk, unset=False, return_query=True)
    site = Site.objects.get(pk=pk)

    for_upload = 'for_upload' in request.GET.keys()
    
    from main.tools.generic import get_dataset_df, download_csv
    from main.tools.projects import get_project

    project = get_project(request)

    #i need to give the project, because quicksand filter-params are saved in the project
    data = get_dataset_df(qs, site, project=project, for_upload=for_upload)
    return download_csv(data, name=f"{site}_analyzedsample_selection.csv")



def get_controls(project=False, authenticated=False):
    """
    all the negative controls (LNC, ENC) as (pk, tag, lnc_batch, enc_batch, probes)
    """
    if project and not authenticated:
        pre_select = AnalyzedSample.objects.filter(project=project)
    else:
        pre_select = AnalyzedSample.objects.all()

    return list(pre_select.filter(
        Q(sample__isnull=True) & Q(tags__in=["LNC", "ENC"])
    ).values_list("pk", "tags", "lnc_batch", "enc_batch", "probes"))


def match_negatives(lnc_negatives, enc_negatives, controls):
    """
    the pks of the controls (see get_controls) that belong to libraries with
    the (lnc_batch, probes) and (enc_batch, probes) combinations
    """
    all_plates = {x[0] for x in lnc_negatives if x[0] is not None}
    lnc_ids = set()
    enc_candidates = defaultdict(list)

    for pk, tag, lnc_batch, enc_batch, probe in controls:
        if tag == "LNC" and (lnc_batch, probe) in lnc_negatives:
            lnc_ids.add(pk)
        if tag == "ENC" and (enc_batch, probe) in enc_negatives:
            enc_candidates[(enc_batch, probe)].append((pk, lnc_batch))

    enc_ids = set()
    for candidates in enc_candidates.values():
        # try to fetch only the ones on the same library plate
        same_plate = [pk for pk, plate in candidates if plate in all_plates]
        # if non exist - fetch from other plates as well
        enc_ids.update(same_plate or [pk for pk, _ in candidates])

    return lnc_ids | enc_ids


def update_query_for_negatives(query, project=False, authenticated=False):
    lnc_negatives = set(query.order_by().values_list("lnc_batch","probes").distinct())
    enc_negatives = set(query.order_by().values_list("enc_batch","probes").distinct())

    # fetch all the controls at once and match them to the batches/probes here
    control_ids = match_negatives(lnc_negatives, enc_negatives, get_controls(project, authenticated))

    # got the ENC and LNC entries, now update the analyzedsamples query again to include LNC and ENC

    updated_query = AnalyzedSample.objects.filter(
        Q(pk__in=query.values_list("pk", flat=True))
        | Q(pk__in=control_ids)
    )

    return updated_query


class AnalyzedSampleForm(forms.ModelForm):
    class Meta:
        model = AnalyzedSample
        fields = ["seqrun", "seqpool", "lane"]


def handle_library_file(request, file):
    df = pd.read_csv(file, sep=",")
    df.drop_duplicates(inplace=True)

    site=tools.generic.get_instance_from_string(request.POST.get('site'))

    # filter for expected/unexpected columns
    expected = AnalyzedSample.table_columns()
    expected.append('object')
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

    return render(
        request,
        "main/modals/sample_modal.html",
        {
            "type": "libraries_confirm",
            "site":site,
            "dataframe": df.fillna("").to_html(
                index=False, classes="table table-striped col-12"
            ),
            "issues": issues,
            "json": df.to_json(),
        },
    )


def save_verified(request):
    df = pd.read_json(io.StringIO(request.POST.get("batch-data")))
    df.convert_dtypes()

    project = Project.objects.get(namespace=request.session["session_project"])
    site = Site.objects.get(pk=int(request.GET.get('site')))

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
        # update the instance if 'object' is provided
        if 'object' in row and row['object']:
            object = tools.generic.get_instance_from_string(row['object'])
        # or create a new object
        else:
            object = AnalyzedSample()
        # set or update
        object.sample = sample
        object.lysate = value_or_none(row["Lysate"])
        object.enc_batch = value_or_none(row["ENC Batch"])
        object.library = row["Library"]
        object.reamp_library = value_or_none(row["Reamp Library"])
        object.lnc_batch = value_or_none(row["LNC Batch"])
        object.molecules_qpcr = value_or_none(row["Molecules (qPCR)"])
        object.efficiency = value_or_none(row["Efficiency"])
        object.capture = value_or_none(row["Capture"])
        object.probes = value_or_none(row["Capture Probe"])      
        object.seqpool = value_or_none(row["Sequencing Pool"])
        object.seqrun = value_or_none(row['Sequencing Run'])
        object.lane = value_or_none(row["Sequencing Lane"])  
        object.tags = value_or_none(row["Tag"])
        object.ena_genbank = value_or_none(row["Nucleotide Archive"])
        object.ena_accession = value_or_none(row["Accession Id"])
        try:      
            object.save()
        except: #unique contraint error
            print('unique constraint error: ',object)
    
    return get_libraries(request, site.pk)


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
    path("sample-search/<int:pk>", search_samples, name='main_analyzedsample_samplesearch'),
    path("dna/<int:pk>", get_site_dna_content, name="main_site_dna_tab"),
    path('download_selection/<int:pk>', download_selection, name='main_analyzedsample_downloadselection')
]
