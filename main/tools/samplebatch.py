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
    if 'filter_layer_pk' in request.session:
        layer = get_instance_from_string(f"layer_{request.session['filter_layer_pk']}")
        query = query.filter(
            Q(sample__layer = layer) | 
            Q(sample__layer__layer = layer) | 
            Q(sample__layer__layer__layer = layer) | 
            Q(layer=layer) | 
            Q(layer__layer=layer) | 
            Q(layer__layer__layer=layer) # NOT ideal, because ony 3 hierarchies...
        )
    # the cultures (several can be selected): culture pks, 'sterile' for samples without culture
    if cultures := request.session.get('filter_culture'):
        condition = Q()
        pks = [x for x in cultures if x != 'sterile']
        if pks:
            condition |= Q(layer__culture__in=pks) | Q(sample__layer__culture__in=pks)
        if 'sterile' in cultures:
            # as Sample.get_layer: the layer of the parent sample, else the own layer (or no layer at all)
            condition |= (Q(sample__isnull=True) & Q(layer__culture__isnull=True)) \
                | (Q(sample__isnull=False) & Q(sample__layer__culture__isnull=True))
        query = query.filter(condition)
    if 'filter_batch_pk' in request.session:
        query = query.filter(Q(batch__pk=request.session['filter_batch_pk']))
    # samples without layer (as Sample.get_layer: the layer of the parent sample, else the own layer), admins only
    if request.session.get('filter_no_layer') and request.user.is_authenticated:
        query = query.filter(
            (Q(sample__isnull=True) & Q(layer__isnull=True))
            | (Q(sample__isnull=False) & Q(sample__layer__isnull=True))
        )
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
