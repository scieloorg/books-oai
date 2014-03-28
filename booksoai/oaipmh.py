from __future__ import unicode_literals

import plumber

from lxml import etree
from datetime import datetime

import pipeline

BASEURL = 'http://books.scielo.org/oai/'


class BadArgumentError(Exception):
    """Raised when a Verb receives wrong args."""


class CannotDisseminateFormatError(Exception):
    """Raised when metadata format is not supported"""


class BadVerbError(Exception):
    """Raised when invalid verb is used"""


class IDDoesNotExistError(Exception):
    """Raised when identifier does not exists"""


class NoRecordsMatchError(Exception):
    """
    Raised when all parameters combined 
    result in empty list of records
    """


class BadResumptionTokenError(Exception):
    """Raised when invalid resumption token is used"""


class IdentifyVerb(object):
    data = {
        'repositoryName': 'SciELO Books',
        'baseURL': BASEURL,
        'protocolVersion': '2.0',
        'adminEmail': 'books@scielo.org',
        'earliestDatestamp': datetime(1909, 04, 01),
        'deletedRecord': 'persistent',
        'granularity': 'YYYY-MM-DD'
    }
    allowed_args = set(('verb',))

    def __init__(self, request_kwargs):
        if set(request_kwargs) != self.allowed_args:
            raise BadArgumentError()

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
        'baseURL': BASEURL,
        'formats': [
            {
                'prefix': 'oai_dc',
                'schema': 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
                'namespace': 'http://www.openarchives.org/OAI/2.0/oai_dc/'
            }
        ]
    }
    allowed_args = set(('identifier', 'verb'))

    def __init__(self, request_kwargs):
        diff = set(request_kwargs) - self.allowed_args
        if diff:
            raise BadArgumentError()
        
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

    required_args = set(('metadataPrefix',))
    allowed_args = set(('from', 'until', 'set', 'resumptionToken', 'metadataPrefix', 'verb'))

    def __init__(self, books, request_kwargs):
        request_set = set(request_kwargs)
        diff = request_set - self.allowed_args

        if diff or not self.required_args.issubset(request_set):
            raise BadArgumentError()
        
        self.data = {
            'request': request_kwargs,
            'baseURL': BASEURL,
            'books': books,
        }

    def __str__(self):
        ppl = plumber.Pipeline(
            pipeline.SetupPipe(),
            pipeline.ResponseDatePipe(),
            pipeline.RequestPipe(),
            pipeline.ListIdentifiersPipe(),
            pipeline.ResumptionTokenPipe(),
            pipeline.TearDownPipe()
        )

        results = ppl.run([self.data])
        xml = ''.join([etree.tostring(record) for record in results])
        return xml


class ListSetsVerb(object):

    allowed_args = set(('resumptionToken', 'verb'))

    def __init__(self, books, request_kwargs):
        diff = set(request_kwargs) - self.allowed_args
        if diff:
            raise BadArgumentError()
        
        self.data = {
            'request': request_kwargs,
            'baseURL': BASEURL,
            'books': books.distinct('publisher'),
        }

    def __str__(self):
        ppl = plumber.Pipeline(
            pipeline.SetupPipe(),
            pipeline.ResponseDatePipe(),
            pipeline.RequestPipe(),
            pipeline.ListSetsPipe(),
            pipeline.ResumptionTokenPipe(),
            pipeline.TearDownPipe()
        )

        results = ppl.run([self.data])
        xml = ''.join([etree.tostring(record) for record in results])
        return xml


class GetRecordVerb(object):

    required_args = set(('identifier', 'metadataPrefix', 'verb'))

    def __init__(self, books, request_kwargs):

        if set(request_kwargs) != self.required_args:
            raise BadArgumentError()
        
        self.data = {
            'request': request_kwargs,
            'baseURL': BASEURL,
            'books': books
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

    required_args = set(('metadataPrefix',))
    allowed_args = set(('from', 'until', 'set', 'resumptionToken', 'metadataPrefix', 'verb'))

    def __init__(self, books, request_kwargs):
        request_set = set(request_kwargs)
        diff = request_set - self.allowed_args

        if diff or not self.required_args.issubset(request_set):
            raise BadArgumentError()
    
        self.data = {
            'request': request_kwargs,
            'baseURL': BASEURL,
            'books': books,
        }

    def __str__(self):
        ppl = plumber.Pipeline(
            pipeline.SetupPipe(),
            pipeline.ResponseDatePipe(),
            pipeline.RequestPipe(),
            pipeline.ListRecordsPipe(),
            pipeline.ResumptionTokenPipe(),
            pipeline.TearDownPipe()
        )

        results = ppl.run([self.data])
        xml = ''.join([etree.tostring(record) for record in results])
        return xml


class CannotDisseminateFormat(object):
    def __init__(self, request_kwargs):
        self.data = {
            'request': request_kwargs,
            'baseURL': BASEURL,
        }

    def __str__(self):
        ppl = plumber.Pipeline(
            pipeline.SetupPipe(),
            pipeline.ResponseDatePipe(),
            pipeline.RequestPipe(),
            pipeline.MetadataFormatErrorPipe(),
            pipeline.TearDownPipe()
        )

        results = ppl.run([self.data])
        xml = results.next()
        return etree.tostring(xml)


class BadVerb(object):

    def __init__(self, request_kwargs):
        self.data = {
            'request': request_kwargs,
            'baseURL': BASEURL,
        }

    def __str__(self):
        ppl = plumber.Pipeline(
            pipeline.SetupPipe(),
            pipeline.ResponseDatePipe(),
            pipeline.RequestPipe(),
            pipeline.BadVerbPipe(),
            pipeline.TearDownPipe()
        )

        results = ppl.run([self.data])
        xml = results.next()
        return etree.tostring(xml)


class IDDoesNotExist(object):

    def __init__(self, request_kwargs):
        self.data = {
            'request': request_kwargs,
            'baseURL': BASEURL,
        }

    def __str__(self):
        ppl = plumber.Pipeline(
            pipeline.SetupPipe(),
            pipeline.ResponseDatePipe(),
            pipeline.RequestPipe(),
            pipeline.IdNotExistPipe(),
            pipeline.TearDownPipe()
        )

        results = ppl.run([self.data])
        xml = results.next()
        return etree.tostring(xml)


class NoRecordsMatch(object):

    def __init__(self, request_kwargs):
        self.data = {
            'request': request_kwargs,
            'baseURL': BASEURL,
        }

    def __str__(self):
        ppl = plumber.Pipeline(
            pipeline.SetupPipe(),
            pipeline.ResponseDatePipe(),
            pipeline.RequestPipe(),
            pipeline.NoRecordsPipe(),
            pipeline.TearDownPipe()
        )

        results = ppl.run([self.data])
        xml = results.next()
        return etree.tostring(xml)


class BadArgument(object):

    def __init__(self, request_kwargs, books=None):
        self.data = {
            'request': request_kwargs,
            'baseURL': BASEURL,
        }

    def __str__(self):
        ppl = plumber.Pipeline(
            pipeline.SetupPipe(),
            pipeline.ResponseDatePipe(),
            pipeline.RequestPipe(),
            pipeline.BadArgumentPipe(),
            pipeline.TearDownPipe()
        )

        results = ppl.run([self.data])
        xml = results.next()
        return etree.tostring(xml)


class BadResumptionToken(object):

    def __init__(self, request_kwargs, books=None):
        self.data = {
            'request': request_kwargs,
            'baseURL': BASEURL,
        }

    def __str__(self):
        ppl = plumber.Pipeline(
            pipeline.SetupPipe(),
            pipeline.ResponseDatePipe(),
            pipeline.RequestPipe(),
            pipeline.BadResumptionTokenPipe(),
            pipeline.TearDownPipe()
        )

        results = ppl.run([self.data])
        xml = results.next()
        return etree.tostring(xml)
