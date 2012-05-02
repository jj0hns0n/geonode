from django.db import models


class DocumentManager(models.Manager):

    def categories(self):
        return self.filter(file__in=("", None))


class LinkManager(models.Manager):
    def categories(self):
        return self.filter(link__in=("", None))
