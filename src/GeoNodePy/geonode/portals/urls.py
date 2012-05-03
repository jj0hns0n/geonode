from django.conf.urls.defaults import *


urlpatterns = patterns('geonode.portals.views',
    url(r"^$", "portals", name="portals_list"),
    url(r"^create/$", "portal_create", name="portals_add"),
    url(r"^(?P<pk>\d+)/edit/$", "portal_edit", name="portals_edit"),
    url(r"^(?P<pk>\d+)/archive/$", "portal_archive", name="portals_archive"),
    url(r"^(?P<slug>[\w-]+)/customize/$", "portal_customize", name="portals_customize"),
    url(r"^(?P<slug>[\w-]+)/$", "index", name="portals_detail"),
    url(r"^(?P<slug>[\w-]+)/map/add/$", "portal_add_map", name="portals_add_map"),
    url(r"^(?P<slug>[\w-]+)/map/(?P<map_pk>\d+)/toggle/$", "portal_toggle_map", name="portals_toggle_map"),
    url(r"^(?P<slug>[\w-]+)/map/(?P<map_pk>\d+)/remove/$", "portal_remove_map", name="portals_remove_map"),
    url(r"^(?P<slug>[\w-]+)/dataset/add/$", "portal_add_dataset", name="portals_add_dataset"),
    url(r"^(?P<slug>[\w-]+)/dataset/(?P<dataset_pk>\d+)/remove/$", "portal_remove_dataset", name="portals_remove_dataset"),
    url(r"^(?P<slug>[\w-]+)/link/add/$", "portal_add_link", name="portals_add_link"),
    url(r"^(?P<slug>[\w-]+)/link/(?P<link_pk>\d+)/delete/$", "portal_delete_link", name="portals_delete_link"),
    url(r"^(?P<slug>[\w-]+)/document/add/$", "portal_add_document", name="portals_add_document"),
    url(r"^(?P<slug>[\w-]+)/document/(?P<document_pk>\d+)/delete/$", "portal_delete_document", name="portals_delete_document"),
)
