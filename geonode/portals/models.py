import os

from django.conf import settings
from django.db import models
from django.template.loader import render_to_string

from geonode.maps.models import Map, Layer
from .managers import DocumentManager, LinkManager, PortalManager


class Portal(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=25, unique=True, null=True)
    summary = models.TextField(blank=True, null=True)
    teaser = models.TextField(blank=True, null=True)

    logo = models.FileField(upload_to="portals/logo/", blank=True, null=True)
    custom_css = models.FileField(upload_to="portals/css/", blank=True, null=True)

    maps = models.ManyToManyField(Map, through="PortalMap")
    datasets = models.ManyToManyField(Layer, through="PortalDataset")

    active = models.BooleanField(default=True)

    objects = PortalManager()

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        # @@ in what context (if any) should this return its subdomain?
        return ("portals_detail", [self.slug])

    def get_context_value(self, name):
        try:
            return self.context_items.get(name=name).value
        except:
            return ""

    def save_css(self):
        css = render_to_string("portals/portal_style.css", {"portal": self})
        if not os.path.exists(os.path.join(settings.MEDIA_ROOT, "portals/css")):
            os.makedirs(os.path.join(settings.MEDIA_ROOT, "portals/css"))

        css_file = open(os.path.join(settings.MEDIA_ROOT, "portals/css/{0}.css".format(self.slug)), "w")
        css_file.write(css)
        css_file.close()

    @property
    def stylesheet(self):
        return "{0}portals/css/{1}.css".format(settings.MEDIA_URL, self.slug)


class PortalMap(models.Model):
    portal = models.ForeignKey(Portal)
    map = models.ForeignKey(Map)
    featured = models.BooleanField(default=False)
    summary = models.TextField(blank=True, null=True)


class PortalDataset(models.Model):
    portal = models.ForeignKey(Portal)
    dataset = models.ForeignKey(Layer)
    featured = models.BooleanField(default=False)
    summary = models.TextField(blank=True, null=True)


class PortalContextItem(models.Model):

    PROPERTY_CHOICES = {
        "body+background-color": "Page background color",
        ".navbar-inner+background-color": "Header background color",
        ".navbar-inner+color": "Header font color",
        "body+font-family": "Body font",
        "body+color": "Body font color",
    }

    portal = models.ForeignKey(Portal, related_name="context_items")
    name = models.SlugField(max_length=150)
    value = models.TextField()

    class Meta:
        unique_together = ("portal", "name")

    def __unicode__(self):
        return "%s: %s" % (self.portal.name, self.name)

    @property
    def selector(self):
        return self.name.split("+")[0]

    @property
    def css_property(self):
        return self.name.split("+")[1]


class Document(models.Model):
    portal = models.ForeignKey(Portal, related_name="documents")
    parent = models.ForeignKey('self', blank=True, null=True, related_name="children")
    file = models.FileField(upload_to="portals/document/", blank=True, null=True)
    label = models.CharField(max_length=255)

    objects = DocumentManager()

    def __unicode__(self):
        return u"%s" % self.label


class Link(models.Model):
    portal = models.ForeignKey(Portal, related_name="links")
    parent = models.ForeignKey('self', blank=True, null=True, related_name="children")
    label = models.CharField(max_length=255)
    link = models.URLField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)

    objects = LinkManager()

    def __unicode__(self):
        return u"%s" % self.label


class Flatpage(models.Model):
    portal = models.ForeignKey(Portal, related_name="flatpages")
    title = models.CharField(max_length=255)
    url = models.CharField(max_length=255, unique=True)
    content = models.TextField()

    def __unicode__(self):
        return u"%s" % self.title
