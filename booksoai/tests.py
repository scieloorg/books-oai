import unittest
from datetime import datetime

from pyramid import testing
from pyramid.httpexceptions import HTTPNotFound


from porteira.porteira import Schema


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_invalid_verb_return_404(self):
        from .views import oai_pmh
        request = testing.DummyRequest()
        request.params = {'verb':'bla'}
        self.assertRaises(HTTPNotFound, oai_pmh, request)

    def test_dummy_identify_return_identify_info(self):
        from .views import oai_pmh
        request = testing.DummyRequest()
        request.params = {'verb':'Identify'}
        response = oai_pmh(request)
        self.assertEqual(response['OAI-PMH']['Identify']['repositoryName'], 'SciELO Books')


class RenderersTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_dummy_identify_verb(self):
        from .renderers import parse_to_xml

        dummy_data = {
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
        
        xml = parse_to_xml(dummy_data)
        sch = Schema()
        self.assertEqual(xml, sch.serialize(dummy_data))
