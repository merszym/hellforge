from main.models import SampleBatch
from main.ajax import get_modal
from django import forms
from django.urls import path
from django.contrib import messages
from main.tools.generic import get_instance_from_string
from django.db.models import Q

def filter_samples(request, query):
    # check if registered, else filter for project only
    if not request.user.is_authenticated:
        from main.tools.projects import get_project
        project = get_project(request)
        query = query.filter(project=project)

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


urlpatterns = [
    path("<int:pk>/update", update, name="main_samplebatch_update"),
]
