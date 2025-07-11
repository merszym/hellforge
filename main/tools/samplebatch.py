from main.models import SampleBatch
from main.ajax import get_modal
from django import forms
from django.urls import path
from django.contrib import messages
from main.tools.generic import get_instance_from_string
from django.db.models import Q

def unset_sample_filters(request):
    request.session.pop('filter_layer_pk','')
    request.session.pop('filter_culture_pk','')
    request.session.pop('filter_analyzed','')
    request.session.pop('filter_combine','')


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
            Q(layer=layer) | Q(sample__layer = layer) | Q(layer__layer=layer) | Q(layer__layer__layer=layer) # NOT ideal, because ony 3 hierarchies...
        )
    # we have the culture filter in request.session
    if 'filter_culture_pk' in request.session:
        culture = get_instance_from_string(f"culture_{request.session['filter_culture_pk']}")
        query = query.filter(
            Q(layer__culture=culture) | Q(sample__layer__culture = culture)
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
