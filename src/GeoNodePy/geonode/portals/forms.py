from django import forms

from .models import Portal, PortalContextItem


class PortalForm(forms.ModelForm):

    class Meta:
        model = Portal


class PortalContextItemForm(forms.ModelForm):

    class Meta:
        model = PortalContextItem
