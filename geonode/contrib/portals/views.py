import json

from django.core.xheaders import populate_xheaders

from django.conf import settings
from django.forms.formsets import formset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader, RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

from geonode.core.maps.models import Map
from .forms import (DocumentForm, FlatpageForm, LinkForm,
    PortalForm, PortalContextItemForm, PortalDatasetForm, PortalMapForm,
    PortalSummaryForm)
from .models import Flatpage, Portal, PortalMap, PortalDataset, PortalContextItem


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
    featured_datasets = PortalDataset.objects.filter(portal=portal, featured=True)
    datasets = PortalDataset.objects.filter(portal=portal, featured=False)

    extra_context = {}

    if request.user.is_staff:
        extra_context["portal_customize_snippet"] = portal_customize(request, portal.slug).content

    return render_to_response("portals/index.html",
        {
            "portal": portal,
            "featured_maps": featured_maps,
            "maps": maps,
            "featured_datasets": featured_datasets,
            "datasets": datasets,
        },
        context_instance=RequestContext(request, extra_context)
    )


# This view is called from FlatpageFallbackMiddleware.process_response
# when a 404 is raised, which often means CsrfViewMiddleware.process_view
# has not been called even if CsrfViewMiddleware is installed. So we need
# to use @csrf_protect, in case the template needs {% csrf_token %}.
@csrf_protect
def flatpage(request, url):
    if not url.endswith('/') and settings.APPEND_SLASH:
        return HttpResponseRedirect("%s/" % request.path)
    if not url.startswith('/'):
        url = "/" + url
    f = get_object_or_404(Flatpage, url__exact=url, portal__slug=getattr(request, "portal_slug", ""), portal__active=True)
    t = loader.get_template("portals/flatpage.html")

    # To avoid having to always use the "|safe" filter in flatpage templates,
    # mark the title and content as already safe (since they are raw HTML
    # content in the first place).
    f.title = mark_safe(f.title)
    f.content = mark_safe(f.content)

    c = RequestContext(request, {
        'flatpage': f,
    })
    response = HttpResponse(t.render(c))
    populate_xheaders(request, response, Flatpage, f.id)
    return response


def flatpage_preview(request, slug, flatpage_pk):
    portal = get_object_or_404(Portal, slug=slug)
    flatpage = get_object_or_404(portal.flatpages, pk=flatpage_pk)

    return render_to_response("portals/flatpage.html", {"flatpage": flatpage}, context_instance=RequestContext(request))


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
def portal_manage(request, pk):
    portal = get_object_or_404(Portal.objects.active(), pk=pk)
    featured_maps = PortalMap.objects.filter(portal=portal, featured=True)
    maps = PortalMap.objects.filter(portal=portal, featured=False)
    featured_datasets = PortalDataset.objects.filter(portal=portal, featured=True)
    datasets = PortalDataset.objects.filter(portal=portal, featured=False)

    if request.method == "POST":
        summary_form = PortalSummaryForm(request.POST, instance=portal)
        if summary_form.is_valid():
            summary_form.save()
    else:
        summary_form = PortalSummaryForm(instance=portal)

    return render_to_response("portals/manage.html",
        {
            "portal": portal,
            "featured_maps": featured_maps,
            "maps": maps,
            "featured_datasets": featured_datasets,
            "datasets": datasets,
            "form": summary_form
        },
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
                return redirect("portals_manage", portal.pk)

    else:
        form = PortalMapForm(portal=portal)

    form.fields["map"].queryset = Map.objects.exclude(pk__in=[m.pk for m in portal.maps.all()])

    return render_to_response("portals/map_form.html",
        {
            "portal": portal,
            "form": form
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_edit_map(request, slug, map_pk):
    portal = get_object_or_404(Portal, slug=slug)
    map = get_object_or_404(PortalMap.objects.filter(portal=portal), map__pk=map_pk)

    if request.method == "POST":
        form = PortalMapForm(request.POST, instance=map, portal=portal)
        if form.is_valid():
            form.save()

            return redirect("portals_manage", portal.pk)
    else:
        form = PortalMapForm(instance=map, portal=portal)

    return render_to_response("portals/map_form.html",
        {
            "portal": portal,
            "form": form,
            "map": map
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_toggle_map(request, slug, map_pk):

    portal = get_object_or_404(Portal, slug=slug)
    map = get_object_or_404(PortalMap.objects.filter(portal=portal), map__pk=map_pk)

    map.featured = not map.featured
    map.save()

    return redirect("portals_manage", portal.pk)


@staff_member_required
def portal_remove_map(request, slug, map_pk):

    portal = get_object_or_404(Portal, slug=slug)
    map = get_object_or_404(PortalMap.objects.filter(portal=portal), map__pk=map_pk)

    if request.method == "POST":
        map.delete()
        return redirect("portals_manage", portal.pk)

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
            if request.POST.get("featured"):
                dataset.featured = True
                dataset.save()
            d = {
                "title": dataset.dataset.title,
                "url": dataset.dataset.get_absolute_url()
            }
            if request.is_ajax():
                return HttpResponse(json.dumps({"dataset": d}), mimetype="application/javascript")
            else:
                return redirect("portals_manage", portal.pk)
    else:
        form = PortalDatasetForm(portal=portal)

    return render_to_response("portals/dataset_form.html",
        {
            "portal": portal,
            "form": form
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_edit_dataset(request, slug, dataset_pk):
    portal = get_object_or_404(Portal, slug=slug)
    dataset = get_object_or_404(PortalDataset.objects.filter(portal=portal), dataset__pk=dataset_pk)

    if request.method == "POST":
        form = PortalDatasetForm(request.POST, instance=dataset, portal=portal)
        if form.is_valid():
            form.save()

            return redirect("portals_manage", portal.pk)
    else:
        form = PortalDatasetForm(instance=dataset, portal=portal)

    return render_to_response("portals/dataset_form.html",
        {
            "portal": portal,
            "form": form,
            "dataset": dataset
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_toggle_dataset(request, slug, dataset_pk):

    portal = get_object_or_404(Portal, slug=slug)
    dataset = get_object_or_404(PortalDataset.objects.filter(portal=portal), dataset__pk=dataset_pk)

    dataset.featured = not dataset.featured
    dataset.save()

    return redirect("portals_manage", portal.pk)


@staff_member_required
def portal_remove_dataset(request, slug, dataset_pk):

    portal = get_object_or_404(Portal, slug=slug)
    dataset = get_object_or_404(PortalDataset.objects.filter(portal=portal), dataset__pk=dataset_pk)

    if request.method == "POST":
        dataset.delete()
        return redirect("portals_manage", portal.pk)

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
                return redirect("portals_manage", portal.pk)
        elif request.is_ajax():
            return HttpResponse(
                json.dumps({"success": False, "error": form.errors}),
                mimetype="application/javascript"
            )
    else:
        form = LinkForm(portal=portal)

    return render_to_response("portals/link_form.html",
        {
            "portal": portal,
            "form": form
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_edit_link(request, slug, link_pk):

    portal = get_object_or_404(Portal, slug=slug)
    link = get_object_or_404(portal.links, pk=link_pk)

    if request.method == "POST":
        form = LinkForm(request.POST, instance=link, portal=portal)
        if form.is_valid:
            form.save()
            return redirect("portals_manage", portal.pk)
    else:
        form = LinkForm(instance=link, portal=portal)

    return render_to_response("portals/link_form.html",
        {
            "portal": portal,
            "form": form,
            "link": link
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_delete_link(request, slug, link_pk):

    portal = get_object_or_404(Portal, slug=slug)
    link = get_object_or_404(portal.links, pk=link_pk)

    if request.method == "POST":
        link.delete()
        return redirect("portals_manage", portal.pk)

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
                return redirect("portals_manage", portal.pk)
    else:
        form = DocumentForm(portal=portal)

    return render_to_response("portals/document_form.html",
        {
            "portal": portal,
            "form": form
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_edit_document(request, slug, document_pk):

    portal = get_object_or_404(Portal, slug=slug)
    document = get_object_or_404(portal.documents, pk=document_pk)

    if request.method == "POST":
        form = DocumentForm(request.POST, instance=document, portal=portal)
        if form.is_valid:
            form.save()
            return redirect("portals_manage", portal.pk)
    else:
        form = DocumentForm(instance=document, portal=portal)

    return render_to_response("portals/document_form.html",
        {
            "portal": portal,
            "form": form,
            "document": document
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_delete_document(request, slug, document_pk):

    portal = get_object_or_404(Portal, slug=slug)
    document = get_object_or_404(portal.documents, pk=document_pk)

    if request.method == "POST":
        document.delete()
        return redirect("portals_manage", portal.pk)

    return render_to_response("portals/document_delete.html",
        {
            "portal": portal,
            "document": document
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_add_flatpage(request, slug):

    portal = get_object_or_404(Portal, slug=slug)

    if request.method == "POST":
        form = FlatpageForm(request.POST, portal=portal)
        if form.is_valid():
            flatpage = form.save()
            if request.is_ajax():
                f = {
                    "title": flatpage.title,
                    "url": flatpage.url
                    }
                return HttpResponse(json.dumps({"flatpage": f}), mimetype="application/javascript")
            else:
                return redirect("portals_manage", portal.pk)
    else:
        form = FlatpageForm(portal=portal)

    return render_to_response("portals/flatpage_form.html",
        {
            "portal": portal,
            "form": form
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_edit_flatpage(request, slug, flatpage_pk):

    portal = get_object_or_404(Portal, slug=slug)
    flatpage = get_object_or_404(portal.flatpages, pk=flatpage_pk)

    if request.method == "POST":
        form = FlatpageForm(request.POST, instance=flatpage, portal=portal)
        if form.is_valid():
            form.save()
            return redirect("portals_manage", portal.pk)
    else:
        form = FlatpageForm(instance=flatpage, portal=portal)

    return render_to_response("portals/flatpage_form.html",
        {
            "portal": portal,
            "form": form,
            "flatpage": flatpage
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_delete_flatpage(request, slug, flatpage_pk):

    portal = get_object_or_404(Portal, slug=slug)
    flatpage = get_object_or_404(portal.flatpages, pk=flatpage_pk)

    if request.method == "POST":
        flatpage.delete()
        return redirect("portals_manage", portal.pk)

    return render_to_response("portals/flatpage_delete.html",
        {
            "portal": portal,
            "flatpage": flatpage
        },
        context_instance=RequestContext(request)
    )
