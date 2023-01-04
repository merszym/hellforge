from django.urls import include, path
from django.conf.urls.static import static
from . import views
from . import urls_ajax
from hellforge import settings

urlpatterns = [
    path('',views.landing, name='landing'),
    path('loc/edit/<int:pk>', views.LocationUpdateView.as_view(), name='location_update'),
    path('loc/add', views.LocationCreateView.as_view(), name='location_add'),
    path('locs', views.LocationListView.as_view(), name='location_list'),
    path('ref/add', views.ReferenceCreateView.as_view(), name='ref_add'),
    path('refs', views.ReferenceListView.as_view(), name='ref_list'),
    path('ref/edit/<int:pk>', views.ReferenceUpdateView.as_view(), name='ref_update'),
    path('site/add', views.SiteCreateView.as_view(), name='site_add'),
    path('sites', views.SiteListView.as_view(), name='site_list'),
    path('site/edit/<int:pk>', views.SiteUpdateView.as_view(), name='site_update'),
    path('site/edit/desc/<int:pk>', views.SiteDescriptionUpdateView.as_view(), name='site_description_update'),
    path('site/<int:pk>', views.SiteDetailView.as_view(), name='site_detail'),
    path('layer/edit/<int:pk>', views.LayerUpdateView.as_view(), name='layer_update'),
    path('layer/remove/<int:pk>', views.LayerDeleteView.as_view(), name='layer_delete'),
    path('culture/edit/<int:pk>', views.CultureUpdateView.as_view(), name='culture_update'),
    path('culture/add', views.CultureCreateView.as_view(), name='culture_add'),
    path('culture', views.CultureListView.as_view(), name='culture_list'),
    path('culture/<int:pk>', views.CultureDetailView.as_view(), name='culture_detail'),
    path('epoch/edit/<int:pk>', views.EpochUpdateView.as_view(), name='epoch_update'),
    path('epoch/add', views.EpochCreateView.as_view(), name='epoch_add'),
    path('epoch', views.EpochListView.as_view(), name='epoch_list'),
    path('checkpoint/add', views.CheckpointCreateView.as_view(), name='checkpoint_add'),
    path('checkpoint/edit/<int:pk>', views.CheckpointUpdateView.as_view(), name='checkpoint_update'),
    path('tools/', include('main.urls_ajax'))
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()