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
