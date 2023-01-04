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
    path('sites', views.SiteListView.as_view(), name='site_list'),
    path('site/<int:pk>', views.SiteDetailView.as_view(), name='site_detail'),
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