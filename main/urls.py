from django.urls import include, path
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView
from django.conf.urls.static import static
from . import views
from . import urls_ajax
from hellforge import settings

urlpatterns = [
    path("", views.landing, name="landing"),
    path("checkpoint/add", views.CheckpointCreateView.as_view(), name="checkpoint_add"),
    path("checkpoint/edit/<int:pk>", views.CheckpointUpdateView.as_view(), name="checkpoint_update"),
    path("", include("main.urls_ajax")),
    path("<str:project>/", include("main.urls_ajax")),
    path("favicon.ico", RedirectView.as_view(url=staticfiles_storage.url("img/favicon.ico"))),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += staticfiles_urlpatterns()
