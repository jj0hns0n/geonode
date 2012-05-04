import json

from django.forms.formsets import formset_factory
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.utils.translation import ugettext_lazy as _

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

from .forms import (DocumentForm, LinkForm,
    PortalForm, PortalContextItemForm, PortalDatasetForm, PortalMapForm)
from .models import Portal, PortalMap, PortalContextItem


def hosts_callback(request, portal_slug):
    request.portal_slug = portal_slug


def portals(request):

    return render_to_response("portals/portal_list.html",
        {"portal_list": Portal.objects.active(), "portal_archive_list": Portal.objects.archived()},
        context_instance=RequestContext(request)
    )


def index(request, **kwargs):
    """
    Portal Index

    Summary
    Featured Maps
    Full list of maps & datasets
    Documents & links

    Staff will be able to:
    - Add new docs and links
    - Add a new map or dataset, demote a featured map, feature a new map
    - Edit additional info (see portal_edit view)

    """
    if kwargs.get("slug"):
        portal = get_object_or_404(Portal.objects.active(), slug=kwargs.get("slug"))
    elif hasattr(request, "portal_slug"):
        portal = get_object_or_404(Portal.objects.active(), slug=request.portal_slug)

    featured_maps = PortalMap.objects.filter(portal=portal, featured=True)
    maps = PortalMap.objects.filter(portal=portal, featured=False)

    extra_context = {}

    if request.user.is_staff:
        extra_context["portal_customize_snippet"] = portal_customize(request, portal.slug).content

    return render_to_response("portals/index.html",
        {
            "portal": portal,
            "featured_maps": featured_maps,
            "maps": maps
        },
        context_instance=RequestContext(request, extra_context)
    )


@staff_member_required
def portal_create(request):
    if request.method == "POST":
        form = PortalForm(request.POST, request.FILES)
        if form.is_valid():
            portal = form.save()
            # generate css
            portal.save_css()
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
    portal = get_object_or_404(Portal.objects.active(), pk=pk)

    if request.method == "POST":
        form = PortalForm(request.POST, request.FILES, instance=portal)
        if form.is_valid():
            form.save()
            # in case the logo changes, save css
            portal.save_css()
            return redirect("portals_list")

    else:
        form = PortalForm(instance=portal)

    return render_to_response("portals/portal_form.html",
        {"form": form, "portal": portal},
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_archive(request, pk):
    """
    Archive Portal

    Toggles the active status of the portal, leaves all data intact
    """
    portal = get_object_or_404(Portal, pk=pk)

    if request.method == "POST":
        portal.active = portal.active == False
        portal.save()
        return redirect("portals_list")

    return render_to_response("portals/portal_archive.html",
        {"portal": portal},
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_customize(request, slug):
    portal = get_object_or_404(Portal, slug=slug)
    ItemFormSet = formset_factory(PortalContextItemForm, extra=0)

    if request.method == "POST":
        formset = ItemFormSet(request.POST)
        if formset.is_valid():
            for form in formset.forms:
                if form.is_valid():
                    form.save(portal)

            portal.save_css()

            messages.success(request, _("Your changes to the portal's theme were saved"))

            return redirect("portals_detail", portal.slug)

    else:
        form_properties = []
        for choice in PortalContextItem.PROPERTY_CHOICES.keys():
            form_properties.append(
                {"name": PortalContextItem.PROPERTY_CHOICES[choice], "value": portal.get_context_value(choice)}
            )
        formset = ItemFormSet(initial=form_properties)

    return render_to_response("portals/portal_customize.html",
        {"formset": formset, "portal": portal},
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_add_map(request, slug):

    portal = get_object_or_404(Portal, slug=slug)

    if request.method == "POST":
        form = PortalMapForm(request.POST, portal=portal)
        if form.is_valid():
            portalmap = form.save()
            if request.POST.get("featured"):
                portalmap.featured = True
                portalmap.save()
            m = {
                "title": portalmap.map.title,
                "url": portalmap.map.get_absolute_url(),
                "featured": portalmap.featured
            }
            if request.is_ajax():
                return HttpResponse(json.dumps({"map": m}), mimetype="application/javascript")
            else:
                return redirect(portal.get_absolute_url())

    else:
        form = PortalMapForm(portal=portal)

    return render_to_response("portals/map_add.html",
        {
            "portal": portal,
            "form": form
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_toggle_map(request, slug, map_pk):

    portal = get_object_or_404(Portal, slug=slug)
    map = get_object_or_404(PortalMap.objects.filter(portal=portal), map__pk=map_pk)

    map.featured = not map.featured
    map.save()

    return redirect(portal.get_absolute_url())


@staff_member_required
def portal_remove_map(request, slug, map_pk):

    portal = get_object_or_404(Portal, slug=slug)
    map = get_object_or_404(PortalMap.objects.filter(portal=portal), map__pk=map_pk)

    if request.method == "POST":
        map.delete()
        return redirect(portal.get_absolute_url())

    return render_to_response("portals/map_remove.html",
        {
            "portal": portal,
            "map": map.map
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_add_dataset(request, slug):

    portal = get_object_or_404(Portal, slug=slug)

    if request.method == "POST":
        form = PortalDatasetForm(request.POST, portal=portal)
        if form.is_valid():
            dataset = form.save()
            d = {
                "title": dataset.title,
                "url": dataset.get_absolute_url()
            }
            if request.is_ajax():
                return HttpResponse(json.dumps({"dataset": d}), mimetype="application/javascript")
            else:
                return redirect(portal.get_absolute_url())
    else:
        form = PortalDatasetForm(portal=portal)

    return render_to_response("portals/dataset_add.html",
        {
            "portal": portal,
            "form": form
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_remove_dataset(request, slug, dataset_pk):

    portal = get_object_or_404(Portal, slug=slug)
    dataset = get_object_or_404(portal.datasets, dataset__pk=dataset_pk)

    if request.method == "POST":
        dataset.delete()
        return redirect(portal.get_absolute_url())

    return render_to_response("portals/dataset_remove.html",
        {
            "portal": portal,
            "dataset": dataset.dataset
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_add_link(request, slug):

    portal = get_object_or_404(Portal, slug=slug)

    if request.method == "POST":
        form = LinkForm(request.POST, portal=portal)
        if form.is_valid():
            link = form.save()
            if request.is_ajax():
                l = {
                    "label": link.label,
                    "url": link.link
                    }
                return HttpResponse(
                    json.dumps({"link": l, "success": True}),
                    mimetype="application/javascript"
                )
            else:
                return redirect(portal.get_absolute_url())
        elif request.is_ajax():
            return HttpResponse(
                json.dumps({"success": False, "error": form.errors}),
                mimetype="application/javascript"
            )
    else:
        form = LinkForm(portal=portal)

    return render_to_response("portals/link_add.html",
        {
            "portal": portal,
            "form": form
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_delete_link(request, slug, link_pk):

    portal = get_object_or_404(Portal, slug=slug)
    link = get_object_or_404(portal.links, pk=link_pk)

    if request.method == "POST":
        link.delete()
        return redirect(portal.get_absolute_url())

    return render_to_response("portals/link_delete.html",
        {
            "portal": portal,
            "link": link
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_add_document(request, slug):

    portal = get_object_or_404(Portal, slug=slug)

    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES, portal=portal)
        if form.is_valid():
            document = form.save()
            if request.is_ajax():
                l = {
                    "label": document.label,
                    "file": document.get_file_url()
                    }
                return HttpResponse(json.dumps({"document": l}), mimetype="application/javascript")
            else:
                return redirect(portal.get_absolute_url())
    else:
        form = DocumentForm(portal=portal)

    return render_to_response("portals/document_add.html",
        {
            "portal": portal,
            "form": form
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_delete_document(request, slug, document_pk):

    portal = get_object_or_404(Portal, slug=slug)
    document = get_object_or_404(portal.documents, pk=document_pk)

    if request.method == "POST":
        document.delete()
        return redirect(portal.get_absolute_url())

    return render_to_response("portals/document_delete.html",
        {
            "portal": portal,
            "document": document
        },
        context_instance=RequestContext(request)
    )
