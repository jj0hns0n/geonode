from django.views.generic import ListView, CreateView, UpdateView


from .models import Portal, PortalContextItem


class PortalsView(ListView):

    model = Portal


class PortalEditView(UpdateView):

    model = Portal
