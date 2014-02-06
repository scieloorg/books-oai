from __future__ import unicode_literals

from oaipmh import IdentifyVerb, ListMetadataFormatsVerb
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound


@view_config(route_name='oai_pmh', renderer='oai')
def oai_pmh(request):
    verb = request.params.get('verb')
    if verb == 'Identify':
        verb = IdentifyVerb()
    elif verb == 'ListMetadataFormats':
    	verb = ListMetadataFormatsVerb()
    else:
        raise HTTPNotFound()
    return verb

