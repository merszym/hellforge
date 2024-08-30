from main.models import SampleBatch
from main.ajax import get_modal
from django import forms
from django.urls import path
from django.contrib import messages


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
