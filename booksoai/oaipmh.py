from __future__ import unicode_literals

import plumber

from lxml import etree
from datetime import datetime

import pipeline


class IdentifyVerb(object):
    data = {
        'repositoryName': 'SciELO Books',
        'baseURL': 'http://books.scielo.org/oai/',
        'protocolVersion': '2.0',
        'adminEmail': 'books@scielo.org',
        'earliestDatestamp': datetime(1909, 04, 01),
        'deletedRecord': 'persistent',
        'granularity': 'YYYY-MM-DD'
    }

    def __init__(self, **request_kwargs):
        self.data['request'] = request_kwargs

    def __str__(self):
        ppl = plumber.Pipeline(
            pipeline.SetupPipe(),
            pipeline.ResponseDatePipe(),
            pipeline.RequestPipe(),
            pipeline.IdentifyNodePipe(),
            pipeline.TearDownPipe()
        )

        results = ppl.run([self.data])
        xml = results.next()
        return etree.tostring(xml)


class ListMetadataFormatsVerb(object):
    data = {
        'baseURL': 'http://books.scielo.org/oai/',
        'formats': [
            {
                'prefix': 'oai_dc',
                'schema': 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
                'namespace': 'http://www.openarchives.org/OAI/2.0/oai_dc/'
            }
        ]
    }

    def __init__(self, **request_kwargs):
        self.data['request'] = request_kwargs

    def __str__(self):
        ppl = plumber.Pipeline(
            pipeline.SetupPipe(),
            pipeline.ResponseDatePipe(),
            pipeline.RequestPipe(),
            pipeline.ListMetadataFormatsPipe(),
            pipeline.MetadataFormatPipe(),
            pipeline.TearDownPipe()
        )

        results = ppl.run([self.data])
        xml = results.next()
        return etree.tostring(xml)


class ListIdentifiersVerb(object):

    def __init__(self, books, **request_kwargs):
        self.data = {
            'request': request_kwargs,
            'baseURL': 'http://books.scielo.org/oai/',
            'books': books
        }

    def __str__(self):
        ppl = plumber.Pipeline(
            pipeline.SetupPipe(),
            pipeline.ResponseDatePipe(),
            pipeline.RequestPipe(),
            pipeline.ListIdentifiersPipe(),
            pipeline.TearDownPipe()
        )

        results = ppl.run([self.data])
        xml = ''.join([etree.tostring(record) for record in results])
        return xml


class ListSetsVerb(object):

    def __init__(self, books, **request_kwargs):
        self.data = {
            'request': request_kwargs,
            'baseURL': 'http://books.scielo.org/oai/',
            'books': books.distinct('publisher')
        }

    def __str__(self):
        ppl = plumber.Pipeline(
            pipeline.SetupPipe(),
            pipeline.ResponseDatePipe(),
            pipeline.RequestPipe(),
            pipeline.ListSetsPipe(),
            pipeline.TearDownPipe()
        )

        results = ppl.run([self.data])
        xml = ''.join([etree.tostring(record) for record in results])
        return xml


class GetRecordVerb(object):
    def __init__(self, books, **request_kwargs):
        self.data = {
            'request': request_kwargs,
            'baseURL': 'http://books.scielo.org/oai/',
            'book': books
        }

    def __str__(self):
        ppl = plumber.Pipeline(
            pipeline.SetupPipe(),
            pipeline.ResponseDatePipe(),
            pipeline.RequestPipe(),
            pipeline.GetRecordPipe(),
            pipeline.TearDownPipe()
        )

        results = ppl.run([self.data])
        xml = results.next()
        return etree.tostring(xml)


class ListRecordsVerb(object):
    def __init__(self, books, **request_kwargs):
        self.data = {
            'request': request_kwargs,
            'baseURL': 'http://books.scielo.org/oai/',
            'book': books
        }

    def __str__(self):
        ppl = plumber.Pipeline(
            pipeline.SetupPipe(),
            pipeline.ResponseDatePipe(),
            pipeline.RequestPipe(),
            pipeline.ListRecordsPipe(),
            pipeline.TearDownPipe()
        )

        results = ppl.run([self.data])
        xml = ''.join([etree.tostring(record) for record in results])
        return xml


class CannotDisseminateFormatError(object):
    def __init__(self, params):
        self.params = params

    def __str__(self):
        ppl = plumber.Pipeline(
            pipeline.SetupPipe(),
            pipeline.ResponseDatePipe(),
            pipeline.RequestPipe(),
            #pipeline.MetadataFormatErrorPipe()
        )