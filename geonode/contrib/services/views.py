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

import uuid
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext, loader
from django.utils.translation import ugettext as _
from django.utils import simplejson as json
from django.shortcuts import get_object_or_404

from geonode.core.security.views import _perms_info
from geonode.contrib.services.models import Service
from geonode.core.layers.models import Layer
from geonode.core.security.models import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.core.layers.utils import layer_set_permissions
from geoserver.catalog import Catalog
from owslib.wms import WebMapService

logger = logging.getLogger("geonode.core.layers.views")

_user, _password = settings.GEOSERVER_CREDENTIALS

SERVICE_LEV_NAMES = {
    Service.LEVEL_NONE  : _('No Service Permissions'),
    Service.LEVEL_READ  : _('Read Only'),
    Service.LEVEL_WRITE : _('Read/Write'),
    Service.LEVEL_ADMIN : _('Administrative')
}

@login_required
def services(request):
    """
    This view shows the list of services that the logged in user owns
    TODO: Show all that they have permissions for
    """
    services = Service.objects.filter(owner=request.user)
    return render_to_response("services/service_list.html", RequestContext(request, {
        'services': services,
    }))

@login_required
def register_service(request):
    if request.method == "GET":
        return render_to_response('services/service_register.html',
                                  RequestContext(request, {}))

    elif request.method == 'POST':
        # Register a new Service
        try:
            method = request.POST.get('method').upper()
            type = request.POST.get('type').upper()
            url = request.POST.get('url')
            name = request.POST.get('name')
            if "user" in request.POST and "password" in request.POST:
                user = request.POST.get('user')
                password = request.POST.get('password')
            else:
                user = None
                password = None

            # First Check if this service already exists based on the URL
            base_url = url
            try:
                service = Service.objects.get(base_url=base_url)
            except Service.DoesNotExist:
                service = None
            if service is not None:
                return_dict = {}
                if service.owner == request.user:
                    return_dict['service_id'] = service.pk
                    return_dict['msg'] = "This is an existing Service" 
                    return HttpResponse(json.dumps(return_dict), 
                                        mimetype='application/json',
                                        status=200)        
                else:
                    return_dict['msg'] = "A Service already Exists for this URL, and you are not the owner" 
                    return HttpResponse(json.dumps(return_dict), 
                                        mimetype='application/json',
                                        status=400)
            # Then Check that the name is Unique
            try:
                service = Service.objects.get(name=name)
            except Service.DoesNotExist:
                service = None
            if service is not None:
                return_dict = {'msg': "This is an existing service using this name.\nPlease specify a different name."}
                return HttpResponse(json.dumps(return_dict), 
                                    mimetype='application/json',
                                    status=400)
            if method == 'C':
                return _register_cascaded_service(type, url, name, user, password) 
            elif method == 'I':
                return _register_indexed_service(type, url, name, user, password)
            elif method == 'H':
                return _register_harvested_service(type, url, name, user, password)
            elif method == 'X':
                return HttpResponse('Not Implemented (Yet)', status=501)
            elif method == 'L':
                return HttpResponse('Local Services not configurable via API', status=400)
            else:
                return HttpResponse('Invalid method', status=400)
        except:
            logger.error("Unexpected Error", exc_info=1) 
            return HttpResponse('Unexpected Error', status=500)
    elif request.method == 'PUT':
        # Update a previously registered Service
        return HttpResponse('Not Implemented (Yet)', status=501)
    elif request.method == 'DELETE':
        # Delete a previously registered Service
        return HttpResponse('Not Implemented (Yet)', status=501)
    else:
        return HttpResponse('Invalid Request', status = 400)

def _register_cascaded_service(type, url, name, user, password):
    if type == 'WMS':
        # Register the Service with GeoServer to be cascaded
        cat = Catalog(settings.GEOSERVER_BASE_URL + "rest", 
                        _user , _password)
        # Can we always assume that it is geonode?
        geonode_ws = cat.get_workspace("geonode")
        ws = cat.create_wmsstore(name,geonode_ws, user, password)
        ws.capabilitiesURL = url
        ws.type = "WMS"
        cat.save(ws)
        available_resources = ws.get_resources(available=True)
        
        # Save the Service record
        service = Service(type = type,
                            method='C',
                            base_url = url,
                            name = name,
                            owner = user)
        service.save()
        message = "Service %s registered" % service.name
        return_dict = {'status': 'ok', 'msg': message, 
                        'id': service.pk,
                        'available_layers': available_resources}
        return HttpResponse(json.dumps(return_dict), 
                            mimetype='application/json',
                            status=200)        
    elif type == 'WFS':
        # Register the Service with GeoServer to be cascaded
        cat = Catalog(settings.GEOSERVER_BASE_URL + "rest", 
                        _user , _password)
        # Can we always assume that it is geonode?
        geonode_ws = cat.get_workspace("geonode")
        wfs_ds = cat.create_datastore(name)
        connection_params = {
            "WFSDataStoreFactory:MAXFEATURES": "0",
            "WFSDataStoreFactory:TRY_GZIP": "true",
            "WFSDataStoreFactory:PROTOCOL": "false",
            "WFSDataStoreFactory:LENIENT": "true",
            "WFSDataStoreFactory:TIMEOUT": "3000",
            "WFSDataStoreFactory:BUFFER_SIZE": "10",
            "WFSDataStoreFactory:ENCODING": "UTF-8",
            "WFSDataStoreFactory:WFS_STRATEGY": "nonstrict",
            "WFSDataStoreFactory:GET_CAPABILITIES_URL": url,
        }
        if user and password:
            connection_params["WFSDataStoreFactory:USERNAME"] = user
            connection_params["WFSDataStoreFactory:PASSWORD"] = password

        wfs_ds.connection_parameters = connection_params
        cat.save(wfs_ds)
        available_resources = wfs_ds.get_resources(available=True)
        
        # Save the Service record
        service = Service(type = type,
                            method='C',
                            base_url = url,
                            name = name,
                            owner = user)
        service.save()
        message = "Service %s registered" % service.name
        return_dict = {'status': 'ok', 'msg': message, 
                        'id': service.pk,
                        'available_layers': available_resources}
        return HttpResponse(json.dumps(return_dict), 
                            mimetype='application/json',
                            status=200)        
    elif type == 'WCS':
        return HttpResponse('Not Implemented (Yet)', status=501)
    else:
        return HttpResponse(
            'Invalid Method / Type combo: ' + 
            'Only Cascaded WMS, WFS and WCS supported',
            mimetype="text/plain",
            status=400)

def _register_cascaded_layers(user, service, layers, perm_spec):
    if service.type == 'WMS' or service.type == "WFS":
        cat = Catalog(settings.GEOSERVER_BASE_URL + "rest", 
                        _user , _password)
        # Can we always assume that it is geonode? 
        geonode_ws = cat.get_workspace("geonode") 
        store = cat.get_store(service.name,geonode_ws)
        count = 0
        for layer in layers: 
            lyr = cat.get_resource(layer)
            if(lyr == None):
                if service.type == "WMS":
                    resource = cat.create_wmslayer(geonode_ws, store, layer) 
                elif service.type == "WFS":
                    resource = cat.create_wfslayer(geonode_ws, store, layer) 
                new_layer, status = Layer.objects.save_layer_from_geoserver(geonode_ws, 
                                                        store, resource)
                new_layer.owner = user
                new_layer.save()
                if perm_spec:
                    layer_set_permissions(new_layer, perm_spec)
                else:
                    pass # Will be assigned default perms
                count += 1
        message = "%d Layers Registered" % count
        return_dict = {'status': 'ok', 'msg': message }
        return HttpResponse(json.dumps(return_dict),
                            mimetype='application/json',
                            status=200)
    elif service.type == 'WCS':
        return HttpResponse('Not Implemented (Yet)', status=501)
    else:
        return HttpResponse('Invalid Service Type', status=400)


def _register_indexed_service(type, url, name, user, password):
    if type == 'WMS':
        # TODO: Handle for errors from owslib
        wms = WebMapService(url)
        # TODO: Make sure we are parsing all service level metadata
        # TODO: Handle for setting ServiceContactRole
        service = Service(type = type,
                          method='I',
                          base_url = url,
                          name = name,
                          version = wms.identification.version,
                          title = wms.identification.title,
                          abstract = wms.identification.abstract,
                          keywords = ','.join(wms.identification.keywords),
                          online_resource = wms.provider.url,
                          owner=user)
        service.save()
        available_resources = []
        for layer in list(wms.contents):
            available_resources.append(wms[layer].name)
        message = "Service %s registered" % service.name
        return_dict = {'status': 'ok', 'msg': message,
                        'id': service.pk,
                        'available_layers': available_resources}
        return HttpResponse(json.dumps(return_dict),
                            mimetype='application/json',
                            status=200)
    elif type == 'WFS':
        return HttpResponse('Not Implemented (Yet)', status=501)
    elif type == 'WCS':
        return HttpResponse('Not Implemented (Yet)', status=501)
    else:
        return HttpResponse(
            'Invalid Method / Type combo: ' + 
            'Only Indexed WMS, WFS and WCS supported',
            mimetype="text/plain",
            status=400)

def _register_indexed_layers(user, service, layers, perm_spec):
    if service.type == 'WMS':
        wms = WebMapService(service.base_url)
        count = 0
        for layer in layers:
            wms_layer = wms[layer]
            layer_uuid = str(uuid.uuid1())
            if wms_layer.keywords:
                keywords = ""
            else:
                keywords=' '.join(wms_layer.keywords)
            # Need to check if layer already exists??
            saved_layer, created = Layer.objects.get_or_create(name=wms_layer.name,
                defaults=dict(
                    service = service,
                    store=service.name, #??
                    storeType="remoteStore",
                    typename=wms_layer.name,
                    workspace="remoteWorkspace",
                    title=wms_layer.title,
                    abstract=wms_layer.abstract,
                    uuid=layer_uuid,
                    #keywords=keywords,
                    owner=user,
                    geographic_bounding_box = wms_layer.boundingBoxWGS84,
                )
            )
            count += 1
        message = "%d Layers Registered" % count
        return_dict = {'status': 'ok', 'msg': message }
        return HttpResponse(json.dumps(return_dict),
                            mimetype='application/json',
                            status=200)
    elif service.type == 'WFS':
        return HttpResponse('Not Implemented (Yet)', status=501)
    elif service.type == 'WCS':
        return HttpResponse('Not Implemented (Yet)', status=501)
    else:
        return HttpResponse('Invalid Service Type', status=400)

def _register_harvested_service(type, url, name, user, password):
    if type == 'CSW':
        # Make this CSW Agnostic (i.e. Not GeoNetwork specific)
        gn = Layer.objects.gn_catalog
        id, service_uuid = gn.add_harvesting_task('CSW', name, url) 
        service = Service(type = type,
                            method='H',
                            base_url = url,
                            name = name,
                            owner=user,
                            uuid = service_uuid,
                            external_id = id)
        service.save()
        message = "Service %s registered" % service.name
        return_dict = {'status': 'ok', 'msg': message,
                        'id': service.pk,
                        'available_layers': []}
        return HttpResponse(json.dumps(return_dict),
                            mimetype='application/json',
                            status=200)
    else:
        return HttpResponse(
            'Invalid Method / Type combo: ' + 
            'Only Harvested CSW supported',
            mimetype="text/plain",
            status=400
        )

@login_required
def register_layers(request):
    if request.method == 'GET':
        return HttpResponse('Not Implemented (Yet)', status=501)
    elif request.method == 'POST':
        try:
            service_id = request.POST.get("service_id")
            layer_list = request.POST.get("layer_list")
            layers = layer_list.split(',')
            if request.POST.get("permissions"):
                perm_spec= json.loads(request.POST.get("permissions"))
            else:
               perm_spec = None 
            try:
                service = Service.objects.get(pk = int(service_id))
            except Service.DoesNotExist:
                return HttpResponse(
                    'No Service mathing id exists',
                    mimetype="text/plain",
                    status=404
                )
            if service.method == 'C':
                return _register_cascaded_layers(request.user, service, layers, perm_spec)
            elif service.method == 'I':
                return _register_indexed_layers(request.user, service, layers, perm_spec)
            elif service.method == 'X':
                return HttpResponse('Not Implemented (Yet)', status=501)
            elif service.method == 'L':
                return HttpResponse('Local Services not configurable via API', status=400)
            else:
                return HttpResponse('Invalid Service Type', status=400)
        except:
            logger.error("Unexpected Error", exc_info=1) 
            return HttpResponse('Unexpected Error', status=501)
    elif request.method == 'PUT':
        return HttpResponse('Not Implemented (Yet)', status=501)
    elif request.method == 'DELETE':
        return HttpResponse('Not Implemented (Yet)', status=501)
    else:
        return HttpResponse('Invalid Request', status = 400)

def service_detail(request, service_id):
    '''
    This view shows the details of a service 
    '''
    service = get_object_or_404(Service,pk=service_id)
    """
    if not request.user.has_perm('maps.view_service', obj=map):
        return HttpResponse(loader.render_to_string('401.html',
            RequestContext(request, {'error_message':
                _("You are not allowed to view this Service.")})), status=401)
    """
    layers = Layer.objects.filter(service=service) 
    return render_to_response("services/service_detail.html", RequestContext(request, {
        'service': service,
        'layers': layers,
        'permissions_json': json.dumps(_perms_info(service, SERVICE_LEV_NAMES))
    }))

@login_required
def edit_service(request, service_id):
    """
    Edit an existing Service
    Redirects to Service Detail temporarily
    """
    return HttpResponseRedirect(reverse("service_detail", args=[service_id]))

@login_required
def remove_service(request, service_id):
    '''
    Delete a service, and its constituent layers. 
    '''
    service = get_object_or_404(Service,pk=service_id) 

    if not request.user.has_perm('maps.delete_service', obj=service):
        return HttpResponse(loader.render_to_string('401.html', 
            RequestContext(request, {'error_message': 
                _("You are not permitted to remove this service.")})), status=401)

    if request.method == 'GET':
        return render_to_response("services/service_remove.html", RequestContext(request, {
            "service": service
        }))
    elif request.method == 'POST':
        layers = service.layer_set.all()
        for layer in layers:
            layer.delete()
        service.delete()

        return HttpResponseRedirect(reverse("services"))

@login_required
def service_layers(request, service_id):
    """
    Return the layers for a service.
    For now it *only* returns unconfigured layers for WMS/WFS serivces
    TODO: Take a ?list=availble ?list=all ?list=configured
    """
    service = get_object_or_404(Service,pk=service_id)
    if service.owner != request.user:
        return HttpResponse(json.dumps({'msg': 'You are not permitted to configure this service'}), 
                             mimetype='application/json',
                             status=400)
    else:
        if service.type == 'WMS' or service.type == 'WFS':
            cat = Layer.objects.gs_catalog
            store = cat.get_store(service.name)
            if store:
                available_resources = store.get_resources(available=True)
                return_dict = { 'id': service.pk,
                                'available_layers': available_resources}
                return HttpResponse(json.dumps(return_dict), 
                                    mimetype='application/json',
                                    status=200)        
            else:
                return HttpResponse(json.dumps({'msg': 'Store for Service Not Found'}), 
                                 mimetype='application/json',
                                 status=400)
        else:
            return HttpResponse(json.dumps({'msg': 'Method not valid for this service type'}), 
                                 mimetype='application/json',
                                 status=400)

def set_service_permissions(service, perm_spec):
    if "authenticated" in perm_spec:
        service.set_gen_level(AUTHENTICATED_USERS, perm_spec['authenticated'])
    if "anonymous" in perm_spec:
        service.set_gen_level(ANONYMOUS_USERS, perm_spec['anonymous'])
    users = [n for (n, p) in perm_spec['users']]
    service.get_user_levels().exclude(user__username__in = users + [service.owner]).delete()
    for username, level in perm_spec['users']:
        user = User.objects.get(username=username)
        service.set_user_level(user, level)

@login_required
def ajax_service_permissions(request, service_id):
    service = get_object_or_404(Service,pk=service_id) 
    if not request.user.has_perm("maps.change_service_permissions", obj=service):
        return HttpResponse(
            'You are not allowed to change permissions for this service',
            status=401,
            mimetype='text/plain'
        )

    if not request.method == 'POST':
        return HttpResponse(
            'You must use POST for editing service permissions',
            status=405,
            mimetype='text/plain'
        )

    spec = json.loads(request.raw_post_data)
    set_service_permissions(service, spec)

    return HttpResponse(
        "Permissions updated",
        status=200,
        mimetype='text/plain')
