# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

import re
import logging
import hashlib
import random

from django.utils.translation import ugettext_lazy as _

from geonode.security.enumerations import ANONYMOUS_USERS, AUTHENTICATED_USERS

from django.conf import settings
from django.utils import simplejson as json
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.template import RequestContext
from django.shortcuts import render_to_response
from geonode.utils import resolve_object
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseRedirect
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.people.models import Profile
from geonode.documents.models import Document
from django.contrib.sites.models import Site

logger = logging.getLogger("geonode.security.views")

def _view_perms_context(obj, level_names):

    ctx =  obj.get_all_level_info()
    def lname(l):
        return level_names.get(l, _("???"))
    ctx[ANONYMOUS_USERS] = lname(ctx.get(ANONYMOUS_USERS, obj.LEVEL_NONE))
    ctx[AUTHENTICATED_USERS] = lname(ctx.get(AUTHENTICATED_USERS, obj.LEVEL_NONE))

    ulevs = []
    for u, l in ctx['users'].items():
        ulevs.append([u, lname(l)])
    ulevs.sort()
    ctx['users'] = ulevs

    return ctx

def _perms_info(obj, level_names):
    info = obj.get_all_level_info()
    # these are always specified even if none
    info[ANONYMOUS_USERS] = info.get(ANONYMOUS_USERS, obj.LEVEL_NONE)
    info[AUTHENTICATED_USERS] = info.get(AUTHENTICATED_USERS, obj.LEVEL_NONE)
    info['users'] = sorted(info['users'].items())
    info['levels'] = [(i, level_names[i]) for i in obj.permission_levels]
    if hasattr(obj, 'owner') and obj.owner is not None:
        info['owner'] = obj.owner.username
    return info


def _perms_info_json(obj, level_names):
    return json.dumps(_perms_info(obj, level_names))

def resource_permissions(request, type, resource_id):
    try:
        if type == "layer":
            resource = resolve_object(request, Layer, {'id':resource_id}, 'layers.change_layer_permissions')
        elif type == "map":
            resource = resolve_object(request, Map, {'id':resource_id}, 'maps.change_map_permissions')
        elif type == "document":
            resource = resolve_object(request, Document, {'id':resource_id}, 'documents.change_document_permissions')
        else:
            return HttpResponse(
                'Invalid resource type',
                status=401,
                mimetype='text/plain')
    except PermissionDenied:
        # we are handling this in a non-standard way
        return HttpResponse(
            'You are not allowed to change permissions for this resource',
            status=401,
            mimetype='text/plain')

    if request.method == 'POST':
        permission_spec = json.loads(request.body)
        resource.set_permissions(permission_spec)

        return HttpResponse(
            json.dumps({'success': True}),
            status=200,
            mimetype='text/plain'
        )

    elif request.method == 'GET':
        permission_spec = json.dumps(resource.get_all_level_info())
        return HttpResponse(
            json.dumps({'success': True, 'permissions': permission_spec}),
            status=200,
            mimetype='text/plain'
        )
    else:
        return HttpResponse(
            'No methods other than get and post are allowed',
            status=401,
            mimetype='text/plain')


def _create_new_user(user_email, resource):
    random_password = User.objects.make_random_password()
    user_name = re.sub(r'\W', r'', user_email.split('@')[0])
    user_length = len(user_name)
    if user_length > 30:
        user_name = user_name[0:29]
    while len(User.objects.filter(username=user_name)) > 0:
        user_name = user_name[0:user_length-4] + User.objects.make_random_password(length=4, allowed_chars='0123456789')

    new_user, created = User.objects.get_or_create(username=user_name, email=user_email, is_active=False)
    new_user.set_password(random_password)
    new_user.save()

    if created:
        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        activation_key = hashlib.sha1(salt+user_email).hexdigest()
        new_profile, created = Profile.objects.get_or_create(user=new_user, name=new_user.username, email=new_user.email)
        new_profile.activation_key = activation_key
        new_profile.save()
        try:
            _send_permissions_email(user_email, resource, random_password)
        except:
            logger.debug("An error ocurred when sending the mail")
            # TODO How should we handle this?
    return new_user

def _send_permissions_email(user_email, resource,  password):

    current_site = Site.objects.get_current()
    user = User.objects.get(email = user_email)
    profile = Profile.objects.get(user=user)
    owner = resource.owner

    subject = render_to_string('account/email/new_user_subject.txt',
            { 'site': current_site,
              'owner' : (owner.get_profile().name if owner.get_profile().name else owner.email),
              })
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())

    message = render_to_string('account/email/new_user_email.txt',
            { 'activation_key': profile.activation_key,
              'owner': (owner.get_profile().name if owner.get_profile().name else owner.email),
              'title': resource.title,
              'url' : resource.get_absolute_url,
              'site': current_site,
              'username': user.username,
              'password' : password })

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

def activate_registration(request, username, activation_key):
    print request
    user = User.objects.get(username = username)
    if activation_key == user.profile.activation_key:
        user.is_active = True
        user.profile.activation_key = ""
        user.save()
        user.profile.save()
        return render_to_response('account/activate.html',
                          context_instance=RequestContext(request))
    else:
        return render_to_response('account/not_activated.html',
                          context_instance=RequestContext(request))
