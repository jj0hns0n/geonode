import json

from django.core.urlresolvers import reverse

from haystack import indexes

from geonode.maps.models import Layer, Map, Thumbnail


class LayerIndex(indexes.RealTimeSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    name = indexes.CharField(model_attr="name")

    spatial_representation_type = indexes.CharField(model_attr="spatial_representation_type", null=True)

    temporal_extent_start = indexes.DateField(model_attr="temporal_extent_start", null=True)
    temporal_extent_end = indexes.DateField(model_attr="temporal_extent_end", null=True)

    int_type = indexes.CharField()
    json = indexes.CharField(indexed=False)

    def get_model(self):
        return Layer

    def prepare_int_type(self, obj):
        return "layer"

    def prepare_json(self, obj):
        # Still need to figure out how to get the follow data:
        """
        {
            attribution: {
                href: "",
                title: ""
            },
            iid: 0,
            last_modified: "2012-01-10T22:01:27.556976",
            bbox: {
                minx: "-82.744",
                miny: "10.706",
                maxx: "-87.691",
                maxy: "15.031"
            },
        }
        """

        data = {
            "_type": self.prepare_int_type(obj),
            "_display_type": obj.display_type,

            "id": obj.id,
            "uuid": obj.uuid,
            "title": obj.title,
            "abstract": obj.abstract,
            "name": obj.name,
            "storeType": obj.storeType,
            "download_links": obj.download_links(),
            "owner": obj.metadata_author.name,
            "metadata_links": obj.metadata_links,
            "keywords": obj.keywords.split() if obj.keywords else [],
            "thumb": Thumbnail.objects.get_thumbnail(obj),

            "detail": obj.get_absolute_url(),  # @@@ Use Sites Framework?
        }

        if obj.owner:
            data.update({"owner_detail": reverse("profiles.views.profile_detail", args=(obj.owner.username,))})

        return json.dumps(data)


class MapIndex(indexes.RealTimeSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    int_type = indexes.CharField()
    json = indexes.CharField(indexed=False)

    def get_model(self):
        return Map

    def prepare_int_type(self, obj):
        return "map"

    def prepare_json(self, obj):
        # Still need to figure out how to get the follow data:
        """
        {
            iid: 3,
            last_modified: "2011-12-20T17:28:05.584942",
        }
        """

        data = {
            "_type": self.prepare_int_type(obj),
            "_display_type": obj.display_type,

            "id": obj.id,
            "title": obj.title,
            "abstract": obj.abstract,
            "owner": obj.metadata_author.name,
            "keywords": obj.keywords.split() if obj.keywords else [],
            "thumb": Thumbnail.objects.get_thumbnail(obj),

            "detail": obj.get_absolute_url(),
        }

        if obj.owner:
            data.update({"owner_detail": reverse("profiles.views.profile_detail", args=(obj.owner.username,))})

        return data
