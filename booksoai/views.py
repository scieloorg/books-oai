from __future__ import unicode_literals

import re
import oaipmh

from datetime import datetime
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound


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
        raise HTTPNotFound()

    params = request.params.copy()
    if need_books:
        search = {}
        if 'identifier' in params:
            search['identifier'] = params['identifier']

        if 'set' in params:
            _set = params['set']
            _set = _set.replace('-', ' ')
            search['publisher'] = re.compile(_set, re.IGNORECASE)

        if 'from' in params:
            _from = params['from']
            _from = datetime.strptime(_from, '%Y-%m-%d')
            search['datestamp'] = {'$gte': _from}

        if 'until' in params:
            until = params['until']
            until = datetime.strptime(until, '%Y-%m-%d')
            search.setdefault('datestamp', {})['$lte'] = until

        params['books'] = request.db.books.find(search)

    return OaiVerb(**params)

