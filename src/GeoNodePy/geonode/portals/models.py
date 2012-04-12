from django.db import models

from django.contrib.sites.models import Site

from geonode.maps.models import Map, Layer


class Portal(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=25, unique=True, null=True)
    summary = models.TextField(blank=True, null=True)
    teaser = models.TextField(blank=True, null=True)

    site = models.ForeignKey(Site, blank=True, null=True)

    logo = models.FileField(upload_to="portals/logo/", blank=True, null=True)

    maps = models.ManyToManyField(Map, through="PortalMap")
    datasets = models.ManyToManyField(Layer)

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        site = Site.objects.get_current()
        try:
            if site.portal:
                return ("geonode.portals.views.index")
        except:
            pass
        return ("portals_detail", [self.slug])

    def save(self, *args, **kwargs):
        if not self.site:
            site = Site.objects.create(
                domain="{0}.geonode.org".format(self.slug),
                name=self.name
            )
            self.site = site
        super(Portal, self).save(*args, **kwargs)


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
    portal = models.ForeignKey(Portal, related_name="documents")
    file = models.FileField(upload_to="portals/document/")
    label = models.CharField(max_length=255)

    def __unicode__(self):
        return u"%s" % self.label


class Link(models.Model):
    portal = models.ForeignKey(Portal, related_name="links")
    label = models.CharField(max_length=255)
    link = models.URLField()

    def __unicode__(self):
        return u"%s" % self.label
