## samples tagged on images (ImageAnnotation): the viewer is the image-modal (image_modal.html, leaflet)
import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import path
from django.views.decorators.http import require_POST
from main.models import Image, ImageAnnotation, Sample


def image_samples(image):
    """
    the samples that can be tagged on an image: the samples of the batch of the gallery
    """
    batch = getattr(image.gallery, "sample_batch", None)
    return Sample.objects.filter(batch=batch) if batch else Sample.objects.none()


def annotation_data(annotation):
    return {"pk": annotation.pk, "sample": annotation.sample_id, "name": annotation.sample.name, "x": annotation.x, "y": annotation.y}


def image_annotations(image):
    """
    the annotations of an image for the viewer (json)
    """
    return json.dumps([annotation_data(a) for a in image.annotations.select_related("sample").order_by("sample__name")])


@login_required
@require_POST
def save_annotation(request, pk):
    """
    tag a sample on the image (or move it): sample and the relative position x, y (0-1)
    """
    image = Image.objects.get(pk=pk)
    try:
        x, y = float(request.POST.get("x")), float(request.POST.get("y"))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("position missing")
    if not (0 <= x <= 1 and 0 <= y <= 1):
        return HttpResponseBadRequest("the position is outside of the image")
    sample = image_samples(image).filter(pk=request.POST.get("sample")).first()
    if sample is None:
        return HttpResponseBadRequest("the sample is not in the batch of the image")
    annotation, created = ImageAnnotation.objects.update_or_create(image=image, sample=sample, defaults={"x": x, "y": y})
    return JsonResponse(annotation_data(annotation), status=201 if created else 200)


@login_required
@require_POST
def delete_annotation(request, pk):
    ImageAnnotation.objects.filter(pk=pk).delete()
    return JsonResponse({"deleted": pk})


def search_samples(request, pk):
    """
    the samples of the batch of the image (type-to-search for tagging), with the information if they are tagged already
    """
    image = Image.objects.get(pk=pk)
    tagged = set(image.annotations.values_list("sample_id", flat=True))
    samples = image_samples(image).order_by("name")
    if query := request.GET.get("q", "").strip():
        samples = samples.filter(name__icontains=query)
    return JsonResponse([{"pk": s.pk, "name": s.name, "tagged": s.pk in tagged} for s in samples[:20]], safe=False)


urlpatterns = [
    path("image/<int:pk>/save", save_annotation, name="main_annotation_save"),
    path("delete/<int:pk>", delete_annotation, name="main_annotation_delete"),
    path("image/<int:pk>/samples", search_samples, name="main_annotation_samples"),
]
