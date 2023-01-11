from django.urls import path, include
import main.tools as tools
from . import ajax

urlpatterns = [
    path('layer/',       include('main.tools.layers')),
    path('profile/',     include('main.tools.profile')),
    path('synonym/',     include('main.tools.synonym')),
    path('site/',        include('main.tools.site')),
    path('date/',        include('main.tools.dating')),
    path('contact/',     include('main.tools.contact')),
    path('reference/',   include('main.tools.references')),
    path('generic/',     include('main.tools.generic')),
    path('editor/save',        ajax.save_description,         name='ajax_description_save'),
    path('editor/get',         ajax.get_description,          name='ajax_description_get'),
    path('contact/add',        ajax.save_contact,             name='ajax_contact_add'),
    path('contact/search',     ajax.search_contact,           name='ajax_contact_search'),
    path('locs/search',        ajax.search_loc,               name='ajax_loc_search'),
    path('fillmodal',          ajax.fill_modal,               name='ajax_fill_modal'),
    path('upload',             ajax.upload_image,             name='upload'),
    path('download-header',    ajax.download_header,          name='download_header'),
]