from django.urls import path
from . import views
from site_aligner import settings

urlpatterns = [
    path('locs/edit/<int:pk>', views.LocationDetailView.as_view(), name='location_update'),
    path('locs/add', views.LocationCreateView.as_view(), name='location_add'),
    path('locs', views.LocationListView.as_view(), name='location_list')
]
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()