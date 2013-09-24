from django import forms
from django.utils.translation import ugettext_lazy as _

from geonode.core.maps.models import Layer
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

    title = forms.CharField(
        required = True,
        widget = forms.TextInput(attrs={"class": "span5"}),
    )
    url = forms.CharField(
        required = True,
        widget = forms.TextInput(attrs={"class": "span5"}),
    )
    content = forms.CharField(
        required = True,
        widget = forms.Textarea(attrs={"class": "span5"}),
    )

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

    name = forms.CharField(
        required = True,
        widget = forms.TextInput(attrs={"class": "span5"}),
    )
    slug = forms.CharField(
        required = True,
        widget = forms.TextInput(attrs={"class": "span5"}),
    )
    teaser = forms.CharField(
        required = True,
        widget = forms.Textarea(attrs={"class": "span5"}),
    )

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


class PortalDatasetForm(forms.ModelForm):

    class Meta:
        model = PortalDataset

    def __init__(self, *args, **kwargs):
        portal = kwargs.pop("portal")
        super(PortalDatasetForm, self).__init__(*args, **kwargs)
        self.fields["portal"].widget = forms.HiddenInput()
        self.fields["portal"].initial = portal.pk
        global_excluded = [d.dataset.pk for d in PortalDataset.objects.exclude(portal=portal)]
        if kwargs.get("instance"):
            excluded = [l.pk for l in portal.datasets.all() if l.pk != kwargs["instance"].pk]
        else:
            excluded = [l.pk for l in portal.datasets.all()]
        self.fields["dataset"].queryset = Layer.objects.exclude(
            pk__in=excluded
        ).exclude(
            pk__in=global_excluded
        )


class PortalLinkForm(forms.ModelForm):

        class Meta:
            model = Link


class PortalDocumentForm(forms.ModelForm):

        class Meta:
            model = Document
