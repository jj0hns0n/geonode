import re

from django import template

from ..models import Portal, PortalContextItem

register = template.Library()


@register.inclusion_tag("portals/portal_stylesheet.html", takes_context=True)
def portal_stylesheet(context):
    try:
        portal = context["request"].site.portal
    except:
        pass
    else:
        return {"portal": portal}
    try:
        return {"portal": Portal.objects.get(slug=context["request"].portal_slug)}
    except:
        return {"portal": None}


""" Requires Django 1.4
@register.assignment_tag(takes_context=True)
def portal_variable(context, name):
    try:
        var = PortalContextItem.objects.get(portal=context.get("portal", None), name=name)
    except PortalContextItem.DoesNotExist:
        return
    else:
        return var.value
"""


class PortalVariable(template.Node):
    def __init__(self, name, var_name):
        self.name = name
        self.var_name = var_name

    def render(self, context):
        try:
            value = PortalContextItem.objects.get(portal=context.get("portal", None), name=self.name).value
        except PortalContextItem.DoesNotExist:
            value = ""
        context[self.var_name] = value
        return ''


@register.tag
def portal_variable(parser, token):
    # This version uses a regular expression to parse tag contents.
    try:
        # Splitting by None == splitting by spaces.
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires arguments" % token.contents.split()[0])
    m = re.search(r'(.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError("%r tag had invalid arguments" % tag_name)
    format_string, var_name = m.groups()
    if not (format_string[0] == format_string[-1] and format_string[0] in ('"', "'")):
        raise template.TemplateSyntaxError("%r tag's argument should be in quotes" % tag_name)
    return PortalVariable(format_string[1:-1], var_name)
