from django.conf import settings
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, Group
from django.utils import simplejson as json

from geonode.maps.models import Map


class SecurityTest(TestCase):

    #fixtures = ['test_data.json', 'map_data.json']

    def test_batch_permissions(self):
        pass
        # The method being tested is commented out in geonode.utils for now
        """
        specs = {u'layers': [], u'maps': [u'1'], u'permissions': {u'users': [[u'group1', u'layer_readwrite']]}}
        
        c = Client()
        logged_in = c.login(username='admin', password='admin')
        response = c.post("/data/api/batch_permissions", 
                            data=json.dumps(specs),
                            content_type="application/json")

        self.assertEquals(response.status_code, 200)
        
        map = Map.objects.get(pk=1)
        group = Group.objects.get(name='group1')
        self.assertEqual(map.get_group_level(group), u'map_readwrite')
        """
