from django.db import models


class Portal(models.Model):
    name = models.SlugField(max_length=150, unique=True)

    def __unicode__(self):
        return self.name


class PortalContextItem(models.Model):
    portal = models.ForeignKey(Portal)
    name = models.SlugField(max_length=150)
    value = models.TextField()

    class Meta:
        unique_together = ("portal", "name")

    def __unicode__(self):
        return "%s: %s" % (self.portal.name, self.name)
