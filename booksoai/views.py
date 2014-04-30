from __future__ import unicode_literals

import re
import oaipmh

from datetime import datetime
from pyramid.view import view_config


VERBS = {
    'Identify': (oaipmh.IdentifyVerb, False),
    'ListMetadataFormats': (oaipmh.ListMetadataFormatsVerb, False),
    'ListIdentifiers': (oaipmh.ListIdentifiersVerb, True),
    'ListSets': (oaipmh.ListSetsVerb, True),
    'GetRecord': (oaipmh.GetRecordVerb, True),
    'ListRecords': (oaipmh.ListRecordsVerb, True),
}

@view_config(route_name='oai_pmh', renderer='oai')
def oai_pmh(request):
    request_verb = request.params.get('verb')
    try:
        OaiVerb, need_books = VERBS[request_verb]
    except KeyError:
        OaiVerb = oaipmh.BadVerb
        need_books = False

    request_kwargs = request.params.copy()
    base_url = request.url.split('?')[0]
    params = {'request_kwargs': request_kwargs, 'base_url': base_url}
    if need_books:
        try:
            params['books'] = filter_books(request_kwargs, request.db, request.registry.settings)
        except oaipmh.CannotDisseminateFormatError:
            OaiVerb = oaipmh.CannotDisseminateFormat
        except oaipmh.IDDoesNotExistError:
            OaiVerb = oaipmh.IDDoesNotExist
        except oaipmh.NoRecordsMatchError:
            OaiVerb = oaipmh.NoRecordsMatch
        except oaipmh.BadResumptionTokenError:
            OaiVerb = oaipmh.BadResumptionToken
        except ValueError:
            OaiVerb = oaipmh.BadArgument

    try:
        return OaiVerb(**params)
    except oaipmh.BadArgumentError:
        return oaipmh.BadArgument(request_kwargs=request_kwargs, base_url=base_url)


def filter_books(request_kwargs, db, settings):
    start = 0
    search = {}
    resumptionToken = 0
    metadata_prefix = request_kwargs.get('metadataPrefix')
    items_per_page = int(settings.get('items_per_page', 100))

    if metadata_prefix and metadata_prefix != u'oai_dc':
        raise oaipmh.CannotDisseminateFormatError

    if 'identifier' in request_kwargs:
        search['identifier'] = request_kwargs['identifier']
        if not db.books.find_one(search):
            raise oaipmh.IDDoesNotExistError

    if 'set' in request_kwargs:
        _set = request_kwargs['set']
        _set = '^%s$' % _set.replace('-', ' ')
        search['publisher'] = re.compile(_set, re.IGNORECASE)

    if 'from' in request_kwargs:
        _from = request_kwargs['from']
        _from = datetime.strptime(_from, '%Y-%m-%d')
        search['datestamp'] = {'$gte': _from}

    if 'until' in request_kwargs:
        until = request_kwargs['until']
        until = datetime.strptime(until, '%Y-%m-%d')
        search.setdefault('datestamp', {})['$lte'] = until

    if 'resumptionToken' in request_kwargs:
        resumptionToken = int(request_kwargs['resumptionToken'])
        start = items_per_page * resumptionToken

    books = db.books.find(search).sort('datestamp')[start: start + items_per_page]
    count = books.count()
    
    if not count:
        raise oaipmh.NoRecordsMatchError

    if count < start:
        raise oaipmh.BadResumptionTokenError

    return books