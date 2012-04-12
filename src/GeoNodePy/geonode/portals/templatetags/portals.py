from django import template

from django.contrib.sites.models import Site

from ..models import PortalContextItem

register = template.Library()


@register.assignment_tag
def portal_css():
    site = Site.objects.get_current()
    try:
        return site.portal.get_stylesheet()
    except:
        return ""


@register.simple_tag(takes_context=True)
def portal_variable(context, name):
    try:
        var = PortalContextItem.objects.get(portal=context.get("portal", None), name=name)
    except PortalContextItem.DoesNotExist:
        return
    else:
        return var.value
