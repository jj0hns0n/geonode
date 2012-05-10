from django import forms
from django.utils.translation import ugettext_lazy as _

from geonode.maps.models import Layer, Map
from .models import Document, Flatpage, Link, Portal, PortalContextItem, PortalDataset, PortalMap


class DocumentForm(forms.ModelForm):

    class Meta:
        model = Document

    def __init__(self, *args, **kwargs):
        portal = kwargs.pop("portal")
        super(DocumentForm, self).__init__(*args, **kwargs)
        self.fields["portal"].widget = forms.HiddenInput()
        self.fields["portal"].initial = portal.pk


class FlatpageForm(forms.ModelForm):

    class Meta:
        model = Flatpage

    def __init__(self, *args, **kwargs):
        portal = kwargs.pop("portal")
        super(FlatpageForm, self).__init__(*args, **kwargs)
        self.fields["portal"].widget = forms.HiddenInput()
        self.fields["portal"].initial = portal.pk


class LinkForm(forms.ModelForm):

    parent = forms.ModelChoiceField(
        label=_("Category"),
        queryset=Link.objects.categories(),
        required=False
        )

    class Meta:
        model = Link

    def __init__(self, *args, **kwargs):
        portal = kwargs.pop("portal")
        super(LinkForm, self).__init__(*args, **kwargs)
        self.fields["portal"].widget = forms.HiddenInput()
        self.fields["portal"].initial = portal.pk


class PortalForm(forms.ModelForm):

    RESERVED_SLUGS = ("www", "opendri")

    class Meta:
        model = Portal
        exclude = (
            "maps",
            "datasets",
            "active",
            "summary",
            "custom_css"  # @@ this could allow for greater control
        )

    def clean_slug(self):
        slug = self.cleaned_data["slug"]
        if slug in self.RESERVED_SLUGS:
            raise forms.ValidationError(_("This is a reserved word. Please choose another."))
        return slug


class PortalSummaryForm(forms.ModelForm):

    class Meta:
        model = Portal
        exclude = (
            "slug",
            "maps",
            "datasets",
            "active",
            "custom_css",
            "teaser",
            "logo"
        )


class PortalContextItemForm(forms.Form):

    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    value = forms.CharField(max_length=255, required=False)

    def __init__(self, *args, **kwargs):
        super(PortalContextItemForm, self).__init__(*args, **kwargs)

    def save(self, portal):
        data = self.cleaned_data
        name = data["name"]
        key = PortalContextItem.PROPERTY_CHOICES.keys()[
            PortalContextItem.PROPERTY_CHOICES.values().index(name)
        ]
        item, created = PortalContextItem.objects.get_or_create(
            portal=portal,
            name=key,
            defaults={
                "value": data["value"]
            }
        )
        if not created:
            item.value = data["value"]
            item.save()


class PortalMapForm(forms.ModelForm):

    class Meta:
        model = PortalMap

    def __init__(self, *args, **kwargs):
        portal = kwargs.pop("portal")
        super(PortalMapForm, self).__init__(*args, **kwargs)
        self.fields["portal"].widget = forms.HiddenInput()
        self.fields["portal"].initial = portal.pk
        self.fields["map"].queryset = Map.objects.exclude(pk__in=[m.pk for m in portal.maps.all()])


class PortalDatasetForm(forms.ModelForm):

    class Meta:
        model = PortalDataset

    def __init__(self, *args, **kwargs):
        portal = kwargs.pop("portal")
        super(PortalDatasetForm, self).__init__(*args, **kwargs)
        self.fields["portal"].widget = forms.HiddenInput()
        self.fields["portal"].initial = portal.pk
        self.fields["dataset"].queryset = Layer.objects.exclude(pk__in=[l.pk for l in portal.datasets.all()])


class PortalLinkForm(forms.ModelForm):

        class Meta:
            model = Link


class PortalDocumentForm(forms.ModelForm):

        class Meta:
            model = Document
