from django.urls import path
from django.conf.urls.static import static
from . import views
from . import urls_ajax
from hellforge import settings

urlpatterns = [
    path('',views.landing, name='landing'),
    path('locs/edit/<int:pk>', views.LocationUpdateView.as_view(), name='location_update'),
    path('locs/add', views.LocationCreateView.as_view(), name='location_add'),
    path('locs', views.LocationListView.as_view(), name='location_list'),
    path('refs/add', views.ReferenceCreateView.as_view(), name='ref_add'),
    path('refs', views.ReferenceListView.as_view(), name='ref_list'),
    path('refs/edit/<int:pk>', views.ReferenceUpdateView.as_view(), name='ref_update'),
    path('sites/add', views.SiteCreateView.as_view(), name='site_add'),
    path('sites', views.SiteListView.as_view(), name='site_list'),
    path('sites/edit/<int:pk>', views.SiteUpdateView.as_view(), name='site_update'),
    path('sites/edit/desc/<int:pk>', views.SiteDescriptionUpdateView.as_view(), name='site_description_update'),
    path('sites/<int:pk>', views.SiteDetailView.as_view(), name='site_detail'),
    path('layers/edit/<int:pk>', views.LayerUpdateView.as_view(), name='layer_update'),
    path('layers/remove/<int:pk>', views.LayerDeleteView.as_view(), name='layer_delete'),
    path('profiles/remove/<int:pk>', views.ProfileDeleteView.as_view(), name='profile_delete'),
    path('date/remove/<int:pk>', views.DateDeleteView.as_view(), name='date_delete'),
    path('cultures/edit/<int:pk>', views.CultureUpdateView.as_view(), name='culture_update'),
    path('cultures/add', views.CultureCreateView.as_view(), name='culture_add'),
    path('cultures', views.CultureListView.as_view(), name='culture_list'),
    path('cultures/<int:pk>', views.CultureDetailView.as_view(), name='culture_detail'),
    path('epochs/edit/<int:pk>', views.EpochUpdateView.as_view(), name='epoch_update'),
    path('epochs/add', views.EpochCreateView.as_view(), name='epoch_add'),
    path('epochs', views.EpochListView.as_view(), name='epoch_list'),
    path('checkpoints/add', views.CheckpointCreateView.as_view(), name='checkpoint_add'),
    path('checkpoints/edit/<int:pk>', views.CheckpointUpdateView.as_view(), name='checkpoint_update'),
]

urlpatterns.extend(urls_ajax.urlpatterns)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()