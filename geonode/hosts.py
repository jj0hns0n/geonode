from django_hosts import patterns, host

from django.conf import settings

host_patterns = patterns('',
    host(r'(www|opendri)', settings.ROOT_URLCONF, name='www'),
    host(r'(?P<portal_slug>[-\w]+)', 'geonode.contrib.portals.urls_host',
        callback='geonode.contrib.portals.views.hosts_callback', name='portal'),
)
