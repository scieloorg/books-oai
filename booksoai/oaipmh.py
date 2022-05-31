from __future__ import unicode_literals

from datetime import datetime

import plumber
import pipeline


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
        'protocolVersion': '2.0',
        'adminEmail': 'scielo.books@scielo.org',
        'deletedRecord': 'persistent',
        'granularity': 'YYYY-MM-DD'
    }
    allowed_args = set(('verb',))

    def __init__(self, last_book, request_kwargs, base_url):

        if set(request_kwargs) != self.allowed_args:
            raise BadArgumentError()

        self.data['request'] = request_kwargs
        self.data['baseURL'] = base_url
        self.data['earliestDatestamp'] = last_book.get('updated', datetime.now().date().isoformat())

    def __str__(self):
        ppl = plumber.Pipeline(
            pipeline.SetupPipe(),
            pipeline.ResponseDatePipe(),
            pipeline.RequestPipe(),
            pipeline.IdentifyNodePipe(),
            pipeline.TearDownPipe()
        )

        results = ppl.run([self.data])

        return next(results)


class ListMetadataFormatsVerb(object):
    data = {
        'formats': [
            {
                'prefix': 'oai_dc',
                'schema': 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
                'namespace': 'http://www.openarchives.org/OAI/2.0/oai_dc/'
            }
        ]
    }
    allowed_args = set(('identifier', 'verb'))

    def __init__(self, request_kwargs, base_url):
        diff = set(request_kwargs) - self.allowed_args
        if diff:
            raise BadArgumentError()

        self.data['request'] = request_kwargs
        self.data['baseURL'] = base_url

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

        return next(results)


class ListIdentifiersVerb(object):

    allowed_args = set(('from', 'until', 'set', 'resumptionToken', 'metadataPrefix', 'verb'))

    def __init__(self, books, request_kwargs, base_url):
        request_set = set(request_kwargs)
        diff = request_set - self.allowed_args

        if not 'resumptionToken' in request_set and not 'metadataPrefix' in request_set:
            raise BadArgumentError()

        if diff:
            raise BadArgumentError()

        self.data = {
            'request': request_kwargs,
            'baseURL': base_url,
            'books': books,
        }

    def __str__(self):
        ppl = plumber.Pipeline(
            pipeline.SetupPipe(),
            pipeline.ResponseDatePipe(),
            pipeline.RequestPipe(),
            pipeline.ListIdentifiersPipe(),
            pipeline.TearDownPipe()
        )

        result = ppl.run([self.data])

        return next(result)


class ListSetsVerb(object):

    allowed_args = set(('resumptionToken', 'verb'))

    def __init__(self, books, request_kwargs, base_url):
        diff = set(request_kwargs) - self.allowed_args
        if diff:
            raise BadArgumentError()

        self.data = {
            'request': request_kwargs,
            'baseURL': base_url,
            'books': books.distinct('publisher'),
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

        return next(results)


class GetRecordVerb(object):

    required_args = set(('identifier', 'metadataPrefix', 'verb'))

    def __init__(self, books, request_kwargs, base_url):

        if set(request_kwargs) != self.required_args:
            raise BadArgumentError()

        self.data = {
            'request': request_kwargs,
            'baseURL': base_url,
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

        return next(results)


class ListRecordsVerb(object):

    allowed_args = set(('from', 'until', 'set', 'resumptionToken', 'metadataPrefix', 'verb'))

    def __init__(self, books, request_kwargs, base_url):
        request_set = set(request_kwargs)
        diff = request_set - self.allowed_args

        if not 'resumptionToken' in request_set and not 'metadataPrefix' in request_set:
            raise BadArgumentError()

        if diff:
            raise BadArgumentError()

        self.data = {
            'request': request_kwargs,
            'baseURL': base_url,
            'books': books,
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

        return next(results)


class CannotDisseminateFormat(object):
    def __init__(self, request_kwargs, base_url):
        self.data = {
            'request': request_kwargs,
            'baseURL': base_url,
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

        return next(results)


class BadVerb(object):

    def __init__(self, request_kwargs, base_url):
        self.data = {
            'request': request_kwargs,
            'baseURL': base_url,
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

        return next(results)


class IDDoesNotExist(object):

    def __init__(self, request_kwargs, base_url):
        self.data = {
            'request': request_kwargs,
            'baseURL': base_url,
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

        return next(results)


class NoRecordsMatch(object):

    def __init__(self, request_kwargs, base_url):
        self.data = {
            'request': request_kwargs,
            'baseURL': base_url,
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

        return next(results)


class BadArgument(object):

    def __init__(self, request_kwargs, base_url, books=None):
        self.data = {
            'request': request_kwargs,
            'baseURL': base_url,
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

        return next(results)


class BadResumptionToken(object):

    def __init__(self, request_kwargs, base_url, books=None):
        self.data = {
            'request': request_kwargs,
            'baseURL': base_url,
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

        return next(results)
