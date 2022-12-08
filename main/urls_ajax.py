from django.urls import path
import main.tools as tools
from . import ajax

urlpatterns = [
    path('a/editor/save',        ajax.save_description,         name='ajax_description_save'),
    path('a/editor/get',         ajax.get_description,          name='ajax_description_get'),
    path('a/refs/add',           ajax.save_ref,                 name='ajax_ref_add'),
    path('a/contact/add',        ajax.save_contact,             name='ajax_contact_add'),
    path('a/date/add',           tools.dating.add,              name='ajax_date_add'),
    path('a/date/calibrate',     tools.dating.calibrate_c14,    name='ajax_date_cal'),
    path('a/refs/search',        ajax.search_ref,               name='ajax_ref_search'),
    path('a/contact/search',     ajax.search_contact,           name='ajax_contact_search'),
    path('a/cp/search',          ajax.search_cp,                name='ajax_cp_search'),
    path('a/locs/search',        ajax.search_loc,               name='ajax_loc_search'),
    path('a/culture/search',     ajax.search_culture,           name='ajax_culture_search'),
    path('a/culture/add',        ajax.save_culture,             name='ajax_culture_add'),
    path('a/epoch/search',       ajax.search_epoch,             name='ajax_epoch_search'),
    path('a/profile/add/<int:site_id>', ajax.save_profile,      name='ajax_profile_add'),
    path('a/profile/<int:pk>',   ajax.get_profile,              name='ajax_profile_detail'),
    path('a/fillmodal',          ajax.fill_modal,               name='ajax_fill_modal'),
    path('a/layer/add/<int:pid>', tools.layers.add,             name='ajax_layer_add'),
    path('a/layer/remove/<int:profile_id>', tools.layers.remove_other, name='ajax_otherlayer_delete'),
    path('a/layer/clone/<int:pk>', tools.layers.clone,                      name='ajax_layer_clone'),
    path('a/layer/search', tools.layers.search,                             name='ajax_layer_search'),
    path('a/layer/update_pos/<int:site_id>', tools.layers.update_positions, name='ajax_layer_pos_update'),
    path('a/upload', ajax.upload_image,                                     name='upload'),
]