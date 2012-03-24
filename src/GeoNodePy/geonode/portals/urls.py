from django.conf.urls import patterns, url

from .views import PortalsView, PortalEditView

urlpatterns = patterns('',
    url(r"^$", PortalsView.as_view(), name="portals_list"),
    url(r"^(?P<pk>\d+)/$", PortalEditView.as_view(), name="portals_edit"),
)
