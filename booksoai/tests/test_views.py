import unittest

from pyramid import testing
from pyramid.httpexceptions import HTTPNotFound

from booksoai.utils import get_db_connection

settings = {}
settings['mongo_uri'] = 'mongodb://localhost:27017/scielobooks-test'
settings['scielo_uri'] = 'http://books.scielo.org/api/v1/'
settings['db_conn'] = get_db_connection(settings)


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_invalid_verb_return_404(self):
        from booksoai.views import oai_pmh
        request = testing.DummyRequest()
        request.params = {'verb':'bla'}
        self.assertRaises(HTTPNotFound, oai_pmh, request)

    # def test_dummy_identify_return_identify_info(self):
    #     from booksoai.views import oai_pmh
    #     request = testing.DummyRequest()
    #     request.params = {'verb':'Identify'}
    #     response = oai_pmh(request)
    #     self.assertEqual(response['OAI-PMH']['Identify']['repositoryName'], 'SciELO Books')

