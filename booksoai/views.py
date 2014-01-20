from __future__ import unicode_literals

from datetime import datetime

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound


@view_config(route_name='oai_pmh', renderer='oai')
def oai_pmh(request):
    verb = request.params.get('verb')
    if verb == 'Identify':
        data = {
            'OAI-PMH': {
                'responseDate': datetime(2014, 01, 15),
                'Identify': {
                    'repositoryName': 'SciELO Books',
                    'baseURL': 'http://books.scielo.org/oai/',
                    'protocolVersion': 2.0,
                    'adminEmail': 'books@scielo.org',
                    'earliestDatestamp': datetime(1909, 04, 01),
                    'deletedRecord': False,
                    'granularity': 'YYYY-MM-DD'
                }
            }
        }
    else:
        raise HTTPNotFound()
    return data