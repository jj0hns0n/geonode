from django.contrib import admin

from .models import Portal, PortalContextItem, PortalMap, Document, Link


admin.site.register(Portal)
admin.site.register(PortalContextItem)
admin.site.register(PortalMap)
admin.site.register(Document)
admin.site.register(Link)
