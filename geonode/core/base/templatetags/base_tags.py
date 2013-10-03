from django import template
from django.conf import settings

from django.db.models import Count

from agon_ratings.models import Rating
from django.contrib.contenttypes.models import ContentType

from geonode.core.base.models import TopicCategory

register = template.Library()

counts = ['map','layer']
if 'geonode.contrib.documents' in settings.INSTALLED_APPS:
    counts.append('document') 

@register.assignment_tag
def num_ratings(obj):
    ct = ContentType.objects.get_for_model(obj)
    return len(Rating.objects.filter(
                object_id = obj.pk,
                content_type = ct
    ))

@register.assignment_tag
def categories():
    topics = TopicCategory.objects.all()
    for c in counts:
        topics = topics.annotate(**{ '%s_count' % c : Count('resourcebase__%s__category' % c)})
    return topics
    