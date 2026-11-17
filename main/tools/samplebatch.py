import json
from main.models import SampleBatch
from main.ajax import get_modal
from django import forms
from django.urls import path
from django.utils.text import slugify
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from main.tools.generic import get_instance_from_string
from django.db.models import Q

def filter_samples(request, query):
    # not logged in: only the samples of the project, logged in: unless 'In project only' is switched off
    from main.tools.dna_filters import project_only
    if not request.user.is_authenticated or project_only(request):
        query = query.filter(project=project_only(request))

    # we have the sample-filters in request.session
    # (the layer of a sample with a parent sample is the layer of the parent, see Sample.save)
    if 'filter_layer_pk' in request.session:
        layer = get_instance_from_string(f"layer_{request.session['filter_layer_pk']}")
        # the layer and all its sub-layers
        query = query.filter(Q(layer__path__startswith=layer.path))
    # the cultures (several can be selected): culture pks, 'sterile' for samples without culture
    if cultures := request.session.get('filter_culture'):
        condition = Q()
        pks = [x for x in cultures if x != 'sterile']
        if pks:
            condition |= Q(layer__culture__in=pks)
        if 'sterile' in cultures:
            # samples without culture (or without layer)
            condition |= Q(layer__culture__isnull=True)
        query = query.filter(condition)
    if 'filter_batch_pk' in request.session:
        query = query.filter(Q(batch__pk=request.session['filter_batch_pk']))
    # samples without layer, admins only
    if request.session.get('filter_no_layer') and request.user.is_authenticated:
        query = query.filter(Q(layer__isnull=True))
    # filter for analyzed only
    if 'filter_analyzed' in request.session:
        if request.session['filter_analyzed'] == True:
            query = query.filter(
                Q(analyzed_sample__isnull = False)
            ).distinct()

    return query


class SampleBatchForm(forms.ModelForm):
    class Meta:
        model = SampleBatch
        fields = ["name", "sampled_by"]


def update(request, pk):
    object = SampleBatch.objects.get(pk=pk)

    form = SampleBatchForm(request.POST, instance=object)

    if form.is_valid():
        form.save()

    # finally, return the modal
    messages.add_message(
        request,
        messages.SUCCESS,
        f"Update of batch successful",
    )

    request.GET._mutable = True
    request.GET.update({"object": f"{object.model}_{object.pk}", "type": "edit"})

    return get_modal(request)


def download_for_upload(request, pk):
    """
    the samples of the batch in the format of the upload-sheet (Sample.table_columns), to edit and upload again.
    the 'object' column (sample_<pk>) identifies the samples: the upload updates them (also the name)
    """
    from main.models import Sample
    from main.tools.generic import download_csv

    batch = SampleBatch.objects.get(pk=pk)
    # the columns of the upload (the ages are calculated, not uploaded)
    columns = ["object"] + [x for x in Sample.table_columns() if not x.startswith("Sample Age")]

    def row(sample):
        # only the own values of the sample: the parent is the layer (or the fossil), nothing is inherited
        # (a sample with a fossil gets the layer of the fossil, the upload sets it from the fossil)
        return {
            "object": f"sample_{sample.pk}",
            "Layer Name": sample.layer.name if sample.layer and not sample.sample else None,
            "Fossil Remain": sample.sample.name if sample.sample else None,
            "Sample Name": sample.name,
            "Sample Synonyms": ";".join(x.export() for x in sample.synonyms.all()),
            "Sample Type": sample.type,
            "Sample Year of Collection": sample.year_of_collection,
            "Sample Provenience": ";".join(f"{k}:{v}" for k, v in json.loads(sample.provenience).items()) if sample.provenience else None,
        }

    samples = batch.sample.select_related("layer", "sample").prefetch_related("synonyms").order_by("name")
    rows = (row(sample) for sample in samples)
    return download_csv(rows, name=f"{slugify(batch.name)}_for_upload.csv", columns=columns)


urlpatterns = [
    path("<int:pk>/update", update, name="main_samplebatch_update"),
    path("<int:pk>/download-for-upload", login_required(download_for_upload), name="main_samplebatch_downloadforupload"),
]
