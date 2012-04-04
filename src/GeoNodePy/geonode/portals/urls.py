from django.conf.urls.defaults import *


urlpatterns = patterns('geonode.portals.views',
    url(r"^$", "portals", name="portals_list"),
    url(r"^create/$", "portal_create", name="portals_add"),
    url(r"^(?P<pk>\d+)/edit/$", "portal_edit", name="portals_edit"),
    url(r"^(?P<pk>\d+)/$", "portal_detail", name="portals_detail"),
)
