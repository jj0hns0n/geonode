from django.template import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404

from django.contrib.admin.views.decorators import staff_member_required

from .forms import PortalForm
from .models import Portal  # PortalContextItem


def portals(request):

    return render_to_response("portals/portal_list.html",
        {"portal_list": Portal.objects.all()},
        context_instance=RequestContext(request)
    )


def portal_detail(request, pk):
    """
    Portal Detail

    Summary
    Featured Maps
    Full list of maps & datasets
    Documents & links

    Staff will be able to:
    - Add new docs and links
    - Add a new map or dataset, demote a featured map, feature a new map
    - Edit additional info (see portal_edit view)

    """
    portal = get_object_or_404(Portal, pk=pk)

    featured_maps = portal.maps.filter(featured=True)
    maps = portal.maps.filter(featured=False)

    # @@ Featured Maps, all maps and datasets, documents, links

    # @@ In-page forms (for admins): upload documents, add links

    # @@ Available: add map, dataset, demote featured map, feature map

    return render_to_response("portals/portal_detail.html",
        {
            "portal": portal,
            "featured_maps": featured_maps,
            "maps": maps
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_create(request):
    if request.method == "POST":
        form = PortalForm(request.POST, request.FILES)
        if form.is_valid():
            portal = form.save()
            return redirect(portal)

    else:
        form = PortalForm()

    return render_to_response("portals/portal_form.html",
        {"form": form},
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_edit(request, pk):
    """
    Edit Portal

    Most actions are available from detail page (adding maps, links, docs, etc)
    The edit page should allow:
    - Change name
    - Change logos/colors
    - Change navigation items

    """
    portal = get_object_or_404(Portal, pk=pk)

    if request.method == "POST":
        form = PortalForm(request.POST, request.FILES, instance=portal)
        if form.is_valid():
            form.save()
            return redirect("portals_list")

    else:
        form = PortalForm(instance=portal)

    return render_to_response("portals/portal_form.html",
        {"form": form, "portal": portal},
        context_instance=RequestContext(request)
    )
