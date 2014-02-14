from __future__ import unicode_literals

import plumber

from lxml import etree
from datetime import datetime


xmlns = "http://www.openarchives.org/OAI/2.0/"
xsi = "http://www.w3.org/2001/XMLSchema-instance"
schemaLocation = "http://www.openarchives.org/OAI/2.0/ "
schemaLocation += "http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"
attrib = {"{%s}schemaLocation" % xsi: schemaLocation}


class SetupPipe(plumber.Pipe):
    def transform(self, data):
        root = etree.Element("OAI-PMH", nsmap={None:xmlns, 'xsi':xsi}, attrib=attrib)
        return (root, data)


class ResponseDatePipe(plumber.Pipe):
    def transform(self, item):
        xml, data = item
        sub = etree.SubElement(xml, 'responseDate')
        now = datetime.utcnow()
        sub.text = now.strftime('%Y-%m-%dT%H:%M:%SZ')
        return (xml, data)


class RequestPipe(plumber.Pipe):
    def transform(self, item):
        xml, data = item
        verb = data.get('verb')
        sub = etree.SubElement(xml, 'request')
        sub.attrib['verb'] = verb
        sub.text = data.get('baseURL')
        return (xml, data)


class IdentifyNodePipe(plumber.Pipe):
    def transform(self, item):
        xml, data = item
        node = etree.SubElement(xml, 'Identify')
        
        sub = etree.SubElement(node, 'repositoryName')
        sub.text = data.get('repositoryName')

        sub = etree.SubElement(node, 'baseURL')
        sub.text = data.get('baseURL')

        sub = etree.SubElement(node, 'protocolVersion')
        sub.text = data.get('protocolVersion')

        sub = etree.SubElement(node, 'adminEmail')
        sub.text = data.get('adminEmail')

        sub = etree.SubElement(node, 'earliestDatestamp')
        datetime = data.get('earliestDatestamp')
        sub.text = str(datetime.date())

        sub = etree.SubElement(node, 'deletedRecord')
        sub.text = data.get('deletedRecord')

        sub = etree.SubElement(node, 'granularity')
        sub.text = data.get('granularity')

        return (xml, data)


class ListMetadataFormatsPipe(plumber.Pipe):
    def transform(self, item):
        xml, data = item
        etree.SubElement(xml, 'ListMetadataFormats')
        return (xml, data)


class MetadataFormatPipe(plumber.Pipe):
    def transform(self, item):
        xml, data = item
        list_metadata_format = xml.find('ListMetadataFormats')

        for format in data.get('formats'):
            metadata_format = etree.SubElement(list_metadata_format, 'metadataFormat')
            prefix = etree.SubElement(metadata_format, 'metadataPrefix')
            prefix.text = format.get('prefix')

            schema= etree.SubElement(metadata_format, 'schema')
            schema.text = format.get('schema')

            namespace = etree.SubElement(metadata_format, 'metadataNamespace')
            namespace.text = format.get('namespace')

        return (xml, data)


class TearDownPipe(plumber.Pipe):
    def transform(self, item):
        xml, data = item
        return xml

