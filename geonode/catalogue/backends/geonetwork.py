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

import urllib, urllib2, cookielib
from datetime import date
from django.conf import settings
from django.template import Context
from django.template.loader import get_template
from owslib.csw import CatalogueServiceWeb, namespaces
from owslib.util import nspath
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, XML, tostring 

from geonode.catalogue.backends.generic import CatalogueBackend \
    as GenericCatalogueBackend


class CatalogueBackend(GenericCatalogueBackend):
    """GeoNetwork CSW Backend"""

    def __init__(self, *args, **kwargs):
        super(CatalogueBackend, self).__init__(*args, **kwargs)
        self.catalogue.formats = ['Dublin Core', 'TC211']

    def add_harvesting_task(self, type, name, url):
        """
        Configure a GeoNetwork harvesting task using the harvesting services
        """
        self.login()
        harvesting_url = self.base + "srv/en/xml.harvesting.add"
        # TODO Handle for various types of harvesting tasks
        groups = self._get_group_ids()
        tpl = get_template('geonetwork/add_csw_harvesting_task.xml')
        ctx = Context({
            'name': name,
            'url': url,
            'groups': groups,
        })
        doc = tpl.render(ctx)
        headers = {
            "Content-Type": "application/xml; charset=UTF-8",
            "Accept": "test/plain"
        }
        doc = doc.encode("utf-8")
        request = urllib2.Request(harvesting_url, doc, headers)
        response = self.urlopen(request)
        response_xml = XML(response.read())
        id = int(response_xml.get('id'))
        uuid = response_xml.find('site/uuid').text
        # TODO Check For errors
        self.control_harvesting_task('start', [id])
        self.control_harvesting_task('run', [id])
        return id, uuid
   
    def control_harvesting_task(self, action, ids):
        """
        Start/Stop/Run an existing harvesting task
        """
        self.login()
        harvesting_url = "%ssrv/en/xml.harvesting.%s" % (self.base, action) 
        request_xml = Element("request")
        for id in ids:
            id_element = SubElement(request_xml, "id")
            id_element.text = str(id)
        doc = tostring(request_xml)
        headers = {
            "Content-Type": "application/xml; charset=UTF-8",
            "Accept": "test/plain"
        }
        doc = doc.encode("utf-8")
        request = urllib2.Request(harvesting_url, doc, headers)
        response = self.urlopen(request)
        response_xml = XML(response.read())
        #TODO Check for errors
        status_reports = response_xml.findall('id')
        status_return = {}
        for status in status_reports:
            status_return[status.text] = status.get('status')
        return status_return 

    def get_uuids_for_source(self, source):
        """
        Get the UUIDs for a particular source (based on uuid usually)
        This is *horrendously inefficient* to get all and filter,
        But, there doesnt seem to be a way to filter by the source
        http://geonetwork-opensource.org/manuals/trunk/developer/xml_services/metadata_xml_services.html
        """
        self.login()
        search_url = "%ssrv/en/xml.search" % (self.base)
        request = urllib2.Request(search_url)
        response = self.urlopen(request)
        doc = XML(response.read())
        uuids = []
        for record in doc.findall('metadata/{http://www.fao.org/geonetwork}info'):
            if record.find('source').text == source:
                uuids.append(record.find('uuid').text)
        return uuids 

    def gn_guzzle(self, ignore_errors=True, verbosity=1, console=sys.stdout):
        """
        Configure layers/resources harvested into GeoNetwork in GeoNode
        """
        if verbosity > 1:
            print >> console, "Inspecting the configured Harvesting Services ..." 
        # Only Harvested CSW for now ...
        services = Service.objects.filter(method='H', type='CSW')
        num_services = len(services)
        if verbosity > 1:
            msg =  "Found %d services, starting processing" % num_services 
            print >> console, msg
        output = []
        if(_csw is None):
            get_csw()
        for i, service in enumerate(services):
            uuids = self.geonetwork.get_uuids_for_source(service.uuid)
            number = len(uuids)
            for j, uuid in enumerate(uuids): 
                name = uuid
                try:
                    _csw.getrecordbyid(id=[uuid])
                    csw_layer = _csw.records.get(uuid) 
                    name = csw_layer.title
                    new_layer, status = self.save_layer_from_geonetwork(service, uuid, csw_layer)
                except (KeyboardInterrupt, SystemExit): 
                    raise
                except Exception, e:
                    if ignore_errors:
                        status = 'failed'
                        exception_type, error, traceback = sys.exc_info()
                    else:
                        if verbosity > 0:
                            msg = "Stopping process because --strict=True and an error was found."
                            print >> sys.stderr, msg
                        raise Exception('Failed to process resource with UUID %s' % name, e), None, sys.exc_info()[2]

                msg = "[%s] Layer %s (%d/%d %d/%d)" % (status, name, i, num_services, j, number)
                info = {'name': name, 'status': status}
                if status == 'failed':
                    info['traceback'] = traceback
                    info['exception_type'] = exception_type
                    info['error'] = error
                output.append(info)
                if verbosity > 0:
                    print >> console, msg
        return output

    def save_layer_from_geonetwork(self, service, uuid, csw_record):
        workspace = "geonode"# Is it safe to hardcode this? 
        try:
            layer, created = self.get_or_create(uuid=uuid, defaults = {
                "service": service,
                "workspace": workspace, 
                "store": "geonetwork",
                "storeType": "cswRecord",
                "typename": "%s:%s" % (workspace, slugify(csw_record.title).replace('-','_')),
                "title": csw_record.title or 'No title provided',
                "abstract": csw_record.abstract or 'No abstract provided',
                "owner": service.owner,
            })
            layer.owner = service.owner
            layer.abstract = csw_record.abstract or 'No Abstract provided'
            layer.name = csw_record.title
            layer.supplemental_information = csw_record.source or "" # Temporary? 
            layer.distribution_url = csw_record.uri
            # TODO Check all items in from __dict__
            layer.save()
            
            if created:
                layer.set_default_permissions()
                status = 'created'
            else:
                status = 'updated'
            return layer, status
        finally: 
           pass
