from datetime import datetime

from pyramid.view import view_config


@view_config(route_name='teste', renderer='oai')
def teste(request):
    data = {
        'responseDate': datetime.now(),
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
    return data