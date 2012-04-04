from django.db import models

from geonode.maps.models import Map, Layer


class Portal(models.Model):
    name = models.SlugField(max_length=150, unique=True)
    summary = models.TextField(blank=True, null=True)
    teaser = models.TextField(blank=True, null=True)

    logo = models.FileField(upload_to="portals/logo/")

    maps = models.ManyToManyField(Map, through="PortalMap")
    datasets = models.ManyToManyField(Layer)

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ("portals_detail", [self.pk])


class PortalMap(models.Model):
    portal = models.ForeignKey(Portal)
    map = models.ForeignKey(Map)
    featured = models.BooleanField(default=False)


class PortalContextItem(models.Model):
    portal = models.ForeignKey(Portal)
    name = models.SlugField(max_length=150)
    value = models.TextField()

    class Meta:
        unique_together = ("portal", "name")

    def __unicode__(self):
        return "%s: %s" % (self.portal.name, self.name)


class Document(models.Model):
    file = models.FileField(upload_to="portals/document/")
    label = models.CharField(max_length=255)

    def __unicode__(self):
        return u"%s" % self.label


class Link(models.Model):
    label = models.CharField(max_length=255)
    link = models.URLField()

    def __unicode__(self):
        return u"%s" % self.label
