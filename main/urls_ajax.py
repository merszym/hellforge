from django.urls import path, include
import main.tools as tools
from . import ajax

urlpatterns = [
    path('layer/',       include('main.tools.layers')),
    path('profile/',     include('main.tools.profile')),
    path('synonym/',     include('main.tools.synonym')),
    path('editor/save',        ajax.save_description,         name='ajax_description_save'),
    path('editor/get',         ajax.get_description,          name='ajax_description_get'),
    path('refs/add',           ajax.save_ref,                 name='ajax_ref_add'),
    path('refs/modal',         tools.references.get_modal,    name='ajax_ref_modal_get'),
    path('refs/popup',         tools.references.get_popup,    name='ajax_ref_popup_get'),
    path('refs/tablerow',      tools.references.get_tablerow, name='ajax_ref_row_get'),
    path('contact/add',        ajax.save_contact,             name='ajax_contact_add'),
    path('date/add',           tools.dating.add,              name='ajax_date_add'),
    path('date/delete',        tools.dating.delete,           name='ajax_date_unlink'),
    path('date/upload',        tools.dating.batch_upload,     name='ajax_date_batch_upload'),
    path('date/save-batch',    tools.dating.save_verified_batchdata,     name='ajax_save_verified_batchdata'),
    path('date/calibrate',     tools.dating.calibrate_c14,    name='ajax_date_cal'),
    path('date/add_rel',       tools.dating.add_relative,    name='ajax_add_reldate'),
    path('refs/search',        ajax.search_ref,               name='ajax_ref_search'),
    path('contact/search',     ajax.search_contact,           name='ajax_contact_search'),
    path('cp/search',          ajax.search_cp,                name='ajax_cp_search'),
    path('locs/search',        ajax.search_loc,               name='ajax_loc_search'),
    path('culture/search',     ajax.search_culture,           name='ajax_culture_search'),
    path('culture/set',        tools.layers.set_culture,      name='ajax_culture_set'),
    path('culture/remove',     tools.layers.remove_culture,   name='ajax_layer_remove_culture'),
    path('epoch/search',       ajax.search_epoch,             name='ajax_epoch_search'),
    path('fillmodal',          ajax.fill_modal,               name='ajax_fill_modal'),
    path('upload',             ajax.upload_image,             name='upload'),
    path('download-header',    ajax.download_header,          name='download_header'),
]