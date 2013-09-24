from django.contrib.auth.models import User, AnonymousUser, Group
from django.core.urlresolvers import reverse
from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client
from django.conf import settings
from django.utils import simplejson as json

from geonode.core.maps.models import Map

class SecurityTest(TestCase):
    """
    Tests for the Geonode security app.
    """

    def setUp(self):
        self.admin, created = User.objects.get_or_create(username='admin', password='admin', is_superuser=True)


    def test_login_middleware(self):
        """
        Tests the Geonode login required authentication middleware.
        """
        from geonode.core.security.middleware import LoginRequiredMiddleware
        middleware = LoginRequiredMiddleware()

        white_list = [
                      reverse('account_ajax_login'),
                      reverse('account_confirm_email', kwargs=dict(key='test')),
                      reverse('account_login'),
                      reverse('account_password_reset'),
                      reverse('forgot_username'),
                      reverse('layer_acls'),
                      reverse('layer_resolve_user'),
                     ]

        black_list = [
                      reverse('account_signup'),
                      reverse('documents_browse'),
                      reverse('maps_browse'),
                      reverse('layer_browse'),
                      reverse('layer_detail', kwargs=dict(layername='geonode:Test')),
                      reverse('layer_remove', kwargs=dict(layername='geonode:Test')),
                      reverse('profile_browse'),
                      ]

        request = HttpRequest()
        request.user = AnonymousUser()

        # Requests should be redirected to the the `redirected_to` path when un-authenticated user attempts to visit
        # a black-listed url.
        for path in black_list:
            request.path = path
            response = middleware.process_request(request)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.get('Location').startswith(middleware.redirect_to))

        # The middleware should return None when an un-authenticated user attempts to visit a white-listed url.
        for path in white_list:
            request.path = path
            response = middleware.process_request(request)
            self.assertIsNone(response, msg="Middleware activated for white listed path: {0}".format(path))

        c = Client()
        c.login(username='admin', password='admin')
        self.assertTrue(self.admin.is_authenticated())
        request.user = self.admin

        # The middleware should return None when an authenticated user attempts to visit a black-listed url.
        for path in black_list:
            request.path = path
            response = middleware.process_request(request)
            self.assertIsNone(response)


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
