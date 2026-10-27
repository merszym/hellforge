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
    ProjectTag,
)
from django.http import JsonResponse, HttpResponse
from django.urls import path, reverse
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


def paginate_rows(request, object_list):
    """
    paginate the rows of an analysis table (quicksand etc.)
    the rows per page are set in the filters of the DNA tab, the page comes from the page-links (?page=)
    """
    from main.tools.dna_filters import get_per_page

    per_page = get_per_page(request)
    paginator = Paginator(object_list, per_page or max(len(object_list), 1))
    page = paginator.get_page(request.GET.get("page", 1))
    return {"object_list": page, "page_obj": page}


# the text-fields of a library (and the sample name) that are searched by the free-text filter
LIBRARY_SEARCH_FIELDS = [
    "lysate", "enc_batch", "library", "reamp_library", "lnc_batch", "capture", "probes",
    "seqrun", "lane", "seqpool", "tags", "ena_genbank", "ena_accession", "sample__name",
]


def search_libraries(query, text):
    """
    keep the libraries that contain the text in any of their fields (case-insensitive)
    """
    condition = Q()
    for field in LIBRARY_SEARCH_FIELDS:
        condition |= Q(**{f"{field}__icontains": text})
    return query.filter(condition)


def filter_missing_analyses(request, query):
    """
    libraries without results in any of the selected analyses (admins only).
    the negative controls of these libraries are added afterwards, independent of their analyses
    """
    if (missing := request.session.get('filter_missing')) and request.user.is_authenticated:
        analyses = {"quicksand": QuicksandAnalysis, "matthias": HumanDiagnosticPositions, "nedflow": NedflowAnalysis}
        condition = Q()
        for analysis in missing:
            if analysis in analyses:
                condition |= ~Q(pk__in=analyses[analysis].objects.exclude(analyzedsample=None).values("analyzedsample"))
        query = query.filter(condition)
    return query


def filter_libraries(request, query):
    if not request.user.is_authenticated:
        from main.tools.projects import get_project

        project = get_project(request)
        query = query.filter(project=project, qc_pass=True)

    if 'filter_probe' in request.session:
        # several probes can be selected
        probes = request.session['filter_probe']
        if isinstance(probes, str):  # sessions from before the multi-select
            probes = [probes]
        query = query.filter(
            Q(probes__in=probes)
        )
    if request.session.get('filter_search'):
        query = search_libraries(query, request.session['filter_search'])
    query = filter_missing_analyses(request, query)
    # the project-tags (several can be selected, libraries with any of them), only tags of the active project
    if tag_pks := request.session.get('filter_project_tags'):
        from main.tools.projects import get_project
        tags = ProjectTag.objects.filter(pk__in=tag_pks, project=get_project(request))
        if tags:
            query = query.filter(
                Q(pk__in=AnalyzedSample.project_tags.through.objects.filter(projecttag__in=tags).values("analyzedsample"))
            )
    return query

def prefetch_for_table(query, project=None):
    """
    for the library-table only: the analyses are ordered, so that .first in the template uses
    the prefetched data, and the large data-field is not needed for the display.
    the project-tags of the active project are in active_project_tags
    """
    return query.prefetch_related(
        'project',
        Prefetch('project_tags', queryset=ProjectTag.objects.filter(project=project), to_attr='active_project_tags'),
        Prefetch('quicksand_analysis', queryset=QuicksandAnalysis.objects.order_by('pk').defer('data')),
        Prefetch('matthias_analysis', queryset=HumanDiagnosticPositions.objects.defer('data')),
        Prefetch('nedflow_analysis', queryset=NedflowAnalysis.objects.order_by('pk').defer('data')),
    )


def library_rows_context(request, library):
    """
    the context to render the rows of the library-table (analyzedsample-row.html) after editing a library:
    the library, or with ?all=yes (sequencing run of all libraries) all libraries of the site with this run/pool/lane
    """
    libraries = AnalyzedSample.objects.filter(pk=library.pk)
    if request.GET.get("all") == "yes" and library.sample:
        libraries = AnalyzedSample.objects.filter(
            Q(seqrun=library.seqrun) & Q(seqpool=library.seqpool) & Q(lane=library.lane) & Q(sample__site=library.sample.site)
        )
    return {
        "libraries": prefetch_for_table(libraries.select_related(*LIBRARY_LAYER_RELATED), project=tools.projects.get_project(request)),
        "site": library.sample.site if library.sample else None,
        "request": request,
        "probe_names": probe_translations(),
        "project": request.session.get("session_project"),
        "modal_url": reverse("main_modal_get"),
        "toggle_url": reverse("main_project_toggle"),
        "delete_url": reverse("main_generic_delete"),
        "oob": True,
    }


def get_libraries(request, pk, return_query=False):
    """
    from one site, get all the (filtered) samples and display the list of libraries
    """

    object = Site.objects.get(pk=pk)
    project = tools.projects.get_project(request)

    #first, do the whole shebang with the samples again!
    samples_qs = Sample.objects.filter(site=object, domain='mpi_eva') \
        .order_by('sample__name')

    samples = tools.samplebatch.filter_samples(request, samples_qs)

    # the filters are set in the side-panel of the DNA tab (main/tools/dna_filters.py)
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

    query = prefetch_for_table(query, project=project)
    
    #paginator to improve speed
    paginator = Paginator(query, 300)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    response = render(
        request, 
        'main/analyzed_samples/analyzedsample_table.html', 
        {
            'object_list':page_obj, 
            'site':object,
            'probe_names':probe_translations(),
            'total':paginator.count,
            'page':page_number
        }
    )
    return response

def download_selection(request, pk):
    qs = get_libraries(request, pk, return_query=True).prefetch_related("project_tags")
    site = Site.objects.get(pk=pk)

    for_upload = 'for_upload' in request.GET.keys()
    
    from main.tools.generic import get_dataset_df, download_csv
    from main.tools.projects import get_project

    project = get_project(request)

    #i need to give the project, because quicksand filter-params are saved in the project
    data = get_dataset_df(qs, site, project=project, for_upload=for_upload)
    return download_csv(data, name=f"{site}_analyzedsample_selection.csv")



def download_analysis_selection(request, pk, analysis):
    """
    download the libraries of an analysis table (quicksand, matthias, nedflow) with all filters of the DNA tab:
    the libraries of the rows of the table, in the order of the table
    """
    from django.http import Http404
    from main.tools import quicksand, matthias, nedflow
    from main.tools.generic import get_dataset_df, download_csv
    from main.tools.projects import get_project

    tables = {"quicksand": quicksand, "matthias": matthias, "nedflow": nedflow}
    if analysis not in tables:
        raise Http404("unknown analysis")
    site = Site.objects.get(pk=pk)

    rows = tables[analysis].table_rows(request, site)["object_list"]
    order = {pk: n for n, pk in enumerate(dict.fromkeys(entry.analyzedsample_id for entry in rows))}
    libraries = sorted(
        AnalyzedSample.objects.filter(pk__in=order).select_related(*LIBRARY_LAYER_RELATED).prefetch_related("project_tags"),
        key=lambda library: order[library.pk],
    )

    for_upload = 'for_upload' in request.GET.keys()
    #i need to give the project, because quicksand filter-params are saved in the project
    data = get_dataset_df(libraries, site, project=get_project(request), for_upload=for_upload)
    return download_csv(data, name=f"{site}_{analysis}_selection.csv")


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


def set_project_tags(library, project, value):
    """
    set the tags of a library in a project from the upload-sheet ('tag1;tag2'), the tags of other projects stay.
    new tag-names are created, existing ones are found case-insensitive
    """
    names = list(dict.fromkeys(x.strip() for x in str(value or "").split(";") if x.strip()))
    tags = []
    for name in names:
        tag = ProjectTag.objects.filter(project=project, name__iexact=name).first()
        tags.append(tag or ProjectTag.objects.create(project=project, name=name))
    library.project_tags.remove(*library.project_tags.filter(project=project))
    library.project_tags.add(*tags)


@login_required
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
            continue
        # the column is optional (older sheets): if it is there, the library has exactly these tags (in this project)
        if "Project Tags" in row.index:
            set_project_tags(object, project, value_or_none(row["Project Tags"]))
    
    return get_libraries(request, site.pk)


@login_required
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


@login_required
def project_tags_update(request, pk):
    """
    set the project-tags of a library in the active project (from the tag-modal): the selected and the new ones
    """
    object = AnalyzedSample.objects.get(pk=pk)
    project = tools.projects.get_project(request)
    if project and request.method == "POST":
        names = request.POST.getlist("project_tag") + [request.POST.get("new_tags", "")]
        set_project_tags(object, project, ";".join(names))
        messages.add_message(request, messages.SUCCESS, "Update of project tags successful")

    request.GET._mutable = True
    request.GET.update({"object": f"{object.model}_{object.pk}", "type": "tags"})

    from main.ajax import get_modal

    return get_modal(request)


@login_required
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


@login_required
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
    path("<int:pk>/update-project-tags", project_tags_update, name="main_analyzedsample_projecttagupdate"),
    path(
        "<int:pk>/update-seqrun", seqrun_update, name="main_analyzedsample_seqrunupdate"
    ),
    path("<int:pk>/update-qc", qc_toggle, name="main_analyzedsample_qctoggle"),
    path("get-data/<int:pk>", get_libraries, name="main_analyzedsample_getdata"),
    path("dna/<int:pk>", get_site_dna_content, name="main_site_dna_tab"),
    path('download_selection/<int:pk>', download_selection, name='main_analyzedsample_downloadselection'),
    path('download_selection/<int:pk>/<str:analysis>', download_analysis_selection, name='main_analysis_downloadselection')
]
