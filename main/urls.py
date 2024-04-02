from django.urls import include, path
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView
from django.conf.urls.static import static
import main.tools as tools
from . import views
from . import ajax
from hellforge import settings
from . import ajax

urlpatterns = [
    path("", views.landing, name="landing"),
    path("layer/", include("main.tools.layers")),
    path("profile/", include("main.tools.profile")),
    path("synonym/", include("main.tools.synonym")),
    path("site/", include("main.tools.site")),
    path("culture/", include("main.tools.culture")),
    path("epoch/", include("main.tools.epoch")),
    path("date/", include("main.tools.dating")),
    path("contact/", include("main.tools.contact")),
    path("reference/", include("main.tools.references")),
    path("generic/", include("main.tools.generic")),
    path("timeline/", include("main.tools.timeline")),
    path("description/", include("main.tools.description")),
    path("projects/", include("main.tools.projects")),
    path("fauna/", include("main.tools.fauna")),
    path("samples/", include("main.tools.samples")),
    path("analyzed-samples/", include("main.tools.analyzed_samples")),
    path("ajax/", include("main.ajax")),
    path("contact/add", ajax.save_contact, name="ajax_contact_add"),
    path("contact/search", ajax.search_contact, name="ajax_contact_search"),
    path("locs/search", ajax.search_loc, name="ajax_loc_search"),
    path("download-header", ajax.download_header, name="download_header"),
    path(
        "favicon.ico",
        RedirectView.as_view(url=staticfiles_storage.url("img/favicon.ico")),
    ),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += staticfiles_urlpatterns()
