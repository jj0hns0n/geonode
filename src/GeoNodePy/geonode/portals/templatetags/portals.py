from django import template

from ..models import PortalContextItem

register = template.Library()


@register.simple_tag(takes_context=True)
def portal_variable(context, name):
    try:
        var = PortalContextItem.objects.get(portal=context.get("portal", None), name=name)
    except PortalContextItem.DoesNotExist:
        return
    else:
        return var.value
