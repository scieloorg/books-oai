import unittest

from bson import json_util
from pyramid import testing
from pyramid.httpexceptions import HTTPNotFound

from booksoai.views import oai_pmh
from booksoai.utils import get_db_connection

settings = {}
settings['mongo_uri'] = 'mongodb://localhost:27017/scielobooks-test'
settings['scielo_uri'] = 'http://books.scielo.org/api/v1/'
settings['db_conn'] = get_db_connection(settings)


class ViewTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db = settings['db_conn']
        with open('booksoai/tests/fixtures/books.bson') as fixture:
            for line in fixture:
                book = json_util.loads(line)
                db.books.insert(book)

    @classmethod
    def tearDownClass(cls):
        db = settings['db_conn']
        db.connection.drop_database(db.name)

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_invalid_verb_return_404(self):
        request = testing.DummyRequest()
        request.params = {'verb':'bla'}
        self.assertRaises(HTTPNotFound, oai_pmh, request)

    def test_get_record_with_identifier(self):
        request = testing.DummyRequest()
        request.db = settings['db_conn']
        request.params = {'verb': 'GetRecord', 'identifier': '37t'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<identifier>37t</identifier>', resp)
        self.assertIn(
        '<request verb="GetRecord" identifier="37t">http://books.scielo.org/oai/</request>',
        resp)
        self.assertEqual(resp.count('<record>'), 1)
        
    def test_list_records_with_from(self):
        request = testing.DummyRequest()
        request.db = settings['db_conn']
        request.params = {'verb': 'ListRecords', 'from': '2014-02-04'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertEqual(resp.count('<record>'), 2)
        self.assertIn('<datestamp>2014-02-04</datestamp>', resp)
        self.assertIn('<datestamp>2014-02-05</datestamp>', resp)

    def test_list_records_with_from_and_until(self):
        request = testing.DummyRequest()
        request.db = settings['db_conn']
        request.params = {'verb': 'ListRecords', 'from': '2014-02-04', 'until': '2014-02-04'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertEqual(resp.count('<record>'), 1)
        self.assertIn('<datestamp>2014-02-04</datestamp>', resp)

    def test_list_records_with_set(self):
        request = testing.DummyRequest()
        request.db = settings['db_conn']
        request.params = {'verb': 'ListRecords', 'set': 'bla-x-ble'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertEqual(resp.count('<record>'), 1)
        self.assertIn('<setSpec>bla-x-ble</setSpec>', resp)
