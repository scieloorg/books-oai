from __future__ import unicode_literals

import oaipmh
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound


@view_config(route_name='oai_pmh', renderer='oai')
def oai_pmh(request):
    verb = request.params.get('verb')
    if verb == 'Identify':
        verb = oaipmh.IdentifyVerb()
    elif verb == 'ListMetadataFormats':
    	verb = oaipmh.ListMetadataFormatsVerb()
    elif verb == 'ListIdentifiers':
    	books = request.db.books.find()
    	verb = oaipmh.ListIdentifiersVerb(books)
    elif verb == 'ListSets':
        books = request.db.books.find()
        verb = oaipmh.ListSetsVerb(books)
    else:
        raise HTTPNotFound()
    return verb

