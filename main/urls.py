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
    path('sites/add', views.SiteCreateView.as_view(), name='site_add'),
    path('sites', views.SiteListView.as_view(), name='site_list'),
    path('sites/edit/<int:pk>', views.SiteUpdateView.as_view(), name='site_update'),
    path('sites/<int:pk>', views.SiteDetailView.as_view(), name='site_detail'),
    path('layers/edit/<int:pk>', views.LayerUpdateView.as_view(), name='layer_update'),
    path('cultures/edit/<int:pk>', views.CultureUpdateView.as_view(), name='culture_update'),
    path('cultures/add', views.CultureCreateView.as_view(), name='culture_add'),
    path('cultures', views.CultureListView.as_view(), name='culture_list'),
    path('epochs/edit/<int:pk>', views.EpochUpdateView.as_view(), name='epoch_update'),
    path('epochs/add', views.EpochCreateView.as_view(), name='epoch_add'),
    path('epochs', views.EpochListView.as_view(), name='epoch_list'),
    path('date/edit/<int:pk>', views.DateUpdateView.as_view(), name='date_update'),
    path('ajax/refs/add', ajax.save_ref, name='ajax_ref_add'),
    path('ajax/date/add', ajax.save_date, name='ajax_date_add'),
    path('ajax/refs/search', ajax.search_ref, name='ajax_ref_search'),
    path('ajax/locs/search', ajax.search_loc, name='ajax_loc_search'),
    path('ajax/profile/add/<int:site_id>', ajax.save_profile, name='ajax_profile_add'),
    path('ajax/profile/<int:pk>', ajax.get_profile, name='ajax_profile_detail'),
    path('ajax/layer/add/<int:profile_id>', ajax.save_layer, name='ajax_layer_add'),
    path('ajax/layer/update_pos/<int:site_id>', ajax.update_layer_positions, name='ajax_layer_pos_update')
]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()