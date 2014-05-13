from __future__ import unicode_literals

import logging
import plumber
import pyramid

from lxml import etree
from plumber import precondition
from datetime import datetime
from simpleslug import slugfy


logging.basicConfig()
logger = logging.getLogger('Pipeline')

xmlns = "http://www.openarchives.org/OAI/2.0/"
xsi = "http://www.w3.org/2001/XMLSchema-instance"
schemaLocation = "http://www.openarchives.org/OAI/2.0/ "
schemaLocation += "http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"
attrib = {"{%s}schemaLocation" % xsi: schemaLocation}


def deleted_precond(item):
    xml, data = item
    if data.get('deleted'):
        raise plumber.UnmetPrecondition


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
        sub = etree.SubElement(xml, 'request')

        for key, value in data.get('request').items():
            sub.attrib[key] = value
        
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


class HeaderPipe(plumber.Pipe):
    def transform(self, item):
        xml, data = item
        header = etree.SubElement(xml, 'header')
        if data.get('deleted'):
            header.attrib['status'] = 'deleted'

        identifier = etree.SubElement(header, 'identifier')
        identifier.text = data.get('identifier')

        datestamp = etree.SubElement(header, 'datestamp')
        date = data.get('datestamp')
        datestamp.text = date.strftime('%Y-%m-%d')

        set_spec = etree.SubElement(header, 'setSpec')
        set_spec.text = slugfy(data.get('publisher', ''))

        return (xml, data)


class ListIdentifiersPipe(plumber.Pipe):
    def transform(self, item):
        xml, data = item
        sub = etree.SubElement(xml, 'ListIdentifiers')

        ppl = plumber.Pipeline(
            HeaderPipe()
        )
        books = data.get('books')
        items = ((sub, book) for book in books)
        results = ppl.run(items)
        
        for header in results:
            pass

        return (xml, data)


class SetPipe(plumber.Pipe):
    def transform(self, data):
        sets = etree.Element('set')

        set_spec = etree.SubElement(sets, 'setSpec')
        set_spec.text = slugfy(data)
        
        set_name = etree.SubElement(sets, 'setName')
        set_name.text = data

        return sets


class ListSetsPipe(plumber.Pipe):
    def transform(self, item):
        xml, data = item
        sub = etree.SubElement(xml, 'ListSets')

        ppl = plumber.Pipeline(
            SetPipe()
        )
        sets = data.get('books')
        results = ppl.run(sets)

        for _set in results:
            sub.append(_set)

        return (xml, data)


class MetadataPipe(plumber.Pipe):
    xmlns = "http://www.openarchives.org/OAI/2.0/oai_dc/"
    dc = "http://purl.org/dc/elements/1.1/"
    xsi = "http://www.w3.org/2001/XMLSchema-instance"
    schemaLocation = "http://www.openarchives.org/OAI/2.0/oai_dc/"
    schemaLocation += " http://www.openarchives.org/OAI/2.0/oai_dc.xsd"
    attrib = {"{%s}schemaLocation" % xsi: schemaLocation}

    @precondition(deleted_precond)
    def transform(self, item):
        xml, data = item
        metadata = etree.SubElement(xml, 'metadata')
        oai_rec = etree.SubElement(metadata, '{%s}dc' % self.xmlns, 
            nsmap={'oai_dc': self.xmlns, 'dc': self.dc ,'xsi': self.xsi},
            attrib=self.attrib
        )

        title = etree.SubElement(oai_rec, '{%s}title' % self.dc)
        title.text = data.get('title')

        creator = etree.SubElement(oai_rec, '{%s}creator' % self.dc)
        try:
            creator.text = data.get('creators').get('organizer')[0][0]
        except TypeError:
            oai_rec.remove(creator)
            logger.info("Can't get organizer for id %s" % data.get('identifier'))
        
        contributor = etree.SubElement(oai_rec, '{%s}contributor' % self.dc)
        try:
            contributor.text = data.get('creators').get('collaborator')[0][0]
        except TypeError:
            oai_rec.remove(contributor)
            logger.info("Can't get collaborator for id %s" % data.get('identifier'))
        
        description = etree.SubElement(oai_rec, '{%s}description' % self.dc)
        description.text = data.get('description')

        publisher = etree.SubElement(oai_rec, '{%s}publisher' % self.dc)
        publisher.text = data.get('publisher')

        date = etree.SubElement(oai_rec, '{%s}date' % self.dc)
        date.text = data.get('date')

        _type = etree.SubElement(oai_rec, '{%s}type' % self.dc)
        _type.text = 'book'

        for f in data.get('formats', []):
            format = etree.SubElement(oai_rec, '{%s}format' % self.dc)
            format.text = f

        identifier = etree.SubElement(oai_rec, '{%s}identifier' % self.dc)
        identifier.text = 'http://books.scielo.org/id/%s' % data.get('identifier')

        language = etree.SubElement(oai_rec, '{%s}language' % self.dc)
        language.text = data.get('language')

        return (xml, data)


class RecordPipe(plumber.Pipe):
    def transform(self, data):
        record = etree.Element('record')

        ppl = plumber.Pipeline(
            HeaderPipe(),
            MetadataPipe()
        )
        results = ppl.run([(record, data)])

        for result in results:
            pass

        return record


class GetRecordPipe(plumber.Pipe):
    def transform(self, item):
        xml, data = item
        sub = etree.SubElement(xml, 'GetRecord')

        ppl = plumber.Pipeline(
            RecordPipe(),
        )
        results = ppl.run(data.get('books'))
        record = results.next()
        sub.append(record)

        return (xml, data)


class ListRecordsPipe(plumber.Pipe):
    def transform(self, item):
        xml, data = item
        sub = etree.SubElement(xml, 'ListRecords')

        ppl = plumber.Pipeline(
            RecordPipe(),
        )
        results = ppl.run(data.get('books'))
        
        for record in results:
            sub.append(record)

        return (xml, data)


class ResumptionTokenPipe(plumber.Pipe):

    def transform(self, item):
        xml, data = item
        sub = etree.SubElement(xml, 'resumptionToken')

        try:
            total_books = data.get('books').count()
        except (AttributeError, TypeError):
            total_books = len(data.get('books', []))

        settings = pyramid.threadlocal.get_current_registry().settings
        items_per_page = int(settings['items_per_page'])
        resumption_token = int(data['request'].get('resumptionToken', 0))
        finished = items_per_page * (resumption_token + 1) >= total_books
        
        if not finished:
            sub.text = str(resumption_token + 1)
        
        return (xml, data)


class TearDownPipe(plumber.Pipe):
    def transform(self, item):
        xml, data = item
        return xml


class BadVerbPipe(plumber.Pipe):
    def transform(self, item):
        xml, data = item
        sub = etree.SubElement(xml, 'error')
        sub.attrib['code'] = 'badVerb'
        sub.text = 'Illegal OAI verb'
        return (xml, data)


class IdNotExistPipe(plumber.Pipe):
    def transform(self, item):
        xml, data = item
        sub = etree.SubElement(xml, 'error')
        sub.attrib['code'] = 'idDoesNotExist'
        sub.text = 'No matching identifier'
        return (xml, data)


class NoRecordsPipe(plumber.Pipe):
    def transform(self, item):
        xml, data = item
        sub = etree.SubElement(xml, 'error')
        sub.attrib['code'] = 'noRecordsMatch'
        return (xml, data)


class BadArgumentPipe(plumber.Pipe):
    def transform(self, item):
        xml, data = item
        sub = etree.SubElement(xml, 'error')
        sub.attrib['code'] = 'badArgument'
        return (xml, data)


class MetadataFormatErrorPipe(plumber.Pipe):
    def transform(self, item):
        xml, data = item
        sub = etree.SubElement(xml, 'error')
        sub.attrib['code'] = 'cannotDisseminateFormat'
        return (xml, data)


class BadResumptionTokenPipe(plumber.Pipe):
    def transform(self, item):
        xml, data = item
        sub = etree.SubElement(xml, 'error')
        sub.attrib['code'] = 'badResumptionToken'
        return (xml, data)


