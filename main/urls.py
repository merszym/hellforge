from django.urls import path
from . import views
from . import ajax
from site_aligner import settings

urlpatterns = [
    path('locs/edit/<int:pk>', views.LocationUpdateView.as_view(), name='location_update'),
    path('locs/add', views.LocationCreateView.as_view(), name='location_add'),
    path('locs', views.LocationListView.as_view(), name='location_list'),
    path('refs/add', views.ReferenceCreateView.as_view(), name='ref_add'),
    path('refs', views.ReferenceListView.as_view(), name='ref_list'),
    path('refs/edit/<int:pk>', views.ReferenceUpdateView.as_view(), name='ref_update'),
    path('ajax/refs/add', ajax.save_ref, name='ajax_ref_add'),
    path('ajax/refs/search', ajax.search_ref, name='ajax_ref_search')


]
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()