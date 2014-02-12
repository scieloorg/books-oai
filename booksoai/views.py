from __future__ import unicode_literals

import oaipmh
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound


VERBS = {
    'Identify': (oaipmh.IdentifyVerb, False),
    'ListMetadataFormats': (oaipmh.ListMetadataFormatsVerb, False),
    'ListIdentifiers': (oaipmh.ListIdentifiersVerb, True),
    'ListSets': (oaipmh.ListSetsVerb, True),
}

@view_config(route_name='oai_pmh', renderer='oai')
def oai_pmh(request):
    request_verb = request.params.get('verb')
    try:
        OaiVerb, need_books = VERBS[request_verb]
    except KeyError:
        raise HTTPNotFound()

    params = {'books': request.db.books.find()} if need_books else {}

    return OaiVerb(**params)

