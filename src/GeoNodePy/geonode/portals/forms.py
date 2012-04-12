from django import forms

from geonode.maps.models import Map
from .models import Document, Link, Portal, PortalContextItem, PortalMap


class DocumentForm(forms.ModelForm):

    class Meta:
        model = Document

    def __init__(self, *args, **kwargs):
        portal = kwargs.pop("portal")
        super(DocumentForm, self).__init__(*args, **kwargs)
        self.fields["portal"].widget = forms.HiddenInput()
        self.fields["portal"].initial = portal.pk


class LinkForm(forms.ModelForm):

    class Meta:
        model = Link

    def __init__(self, *args, **kwargs):
        portal = kwargs.pop("portal")
        super(LinkForm, self).__init__(*args, **kwargs)
        self.fields["portal"].widget = forms.HiddenInput()
        self.fields["portal"].initial = portal.pk


class PortalForm(forms.ModelForm):

    class Meta:
        model = Portal
        exclude = (
            "summary",
            "maps",
            "datasets",
            "site"
        )


class PortalContextItemForm(forms.ModelForm):

    class Meta:
        model = PortalContextItem


class PortalMapForm(forms.ModelForm):

    class Meta:
        model = PortalMap

    def __init__(self, *args, **kwargs):
        portal = kwargs.pop("portal")
        super(PortalMapForm, self).__init__(*args, **kwargs)
        self.fields["portal"].widget = forms.HiddenInput()
        self.fields["portal"].initial = portal.pk
        self.fields["map"].queryset = Map.objects.exclude(pk__in=[m.pk for m in portal.maps.all()])


class PortalLinkForm(forms.ModelForm):

        class Meta:
            model = Link


class PortalDocumentForm(forms.ModelForm):

        class Meta:
            model = Document
