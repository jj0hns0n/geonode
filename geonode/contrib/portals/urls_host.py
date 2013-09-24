from django.conf.urls.defaults import *

from geonode.urls import urlpatterns as geonode_urls

urlpatterns = patterns("",
    (r"^$", "geonode.contrib.portals.views.index"),
)

urlpatterns += geonode_urls
