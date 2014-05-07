from __future__ import unicode_literals

import unittest

from bson import json_util
from pyramid import testing

from booksoai import oaipmh
from booksoai.views import oai_pmh, filter_books
from booksoai.utils import get_db_connection

settings = {}
settings['mongo_uri'] = 'mongodb://localhost:27017/scielobooks-test'
settings['scielo_uri'] = 'http://books.scielo.org/api/v1/'
settings['db_conn'] = get_db_connection(settings)
settings['items_per_page'] = 2


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

    def test_invalid_verb_return_bad_verb_error(self):
        request = testing.DummyRequest()
        request.params = {'verb':'bla'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<error code="badVerb">Illegal OAI verb</error>', resp)

    def test_get_record_with_identifier(self):
        request = testing.DummyRequest()
        request.db = settings['db_conn']
        request.url = 'http://localhost:6543/oai-pmh?'
        request.params = {'verb': 'GetRecord', 'identifier': '37t', 'metadataPrefix': 'oai_dc'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<identifier>37t</identifier>', resp)
        self.assertIn(
        '<request verb="GetRecord" metadataPrefix="oai_dc" identifier="37t">http://localhost:6543/oai-pmh</request>',
        resp)
        self.assertEqual(resp.count('<record>'), 1)
        
    def test_list_records_with_from(self):
        request = testing.DummyRequest()
        request.registry.settings = settings
        request.db = settings['db_conn']
        request.params = {'verb': 'ListRecords', 'from': '2014-02-04', 'metadataPrefix': 'oai_dc'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertEqual(resp.count('<record>'), 2)
        self.assertIn('<datestamp>2014-02-04</datestamp>', resp)
        self.assertIn('<datestamp>2014-02-05</datestamp>', resp)

    def test_list_records_with_from_and_until(self):
        request = testing.DummyRequest()
        request.registry.settings = settings
        request.db = settings['db_conn']
        request.params = {'verb': 'ListRecords', 'from': '2014-02-04', 'until': '2014-02-04', 'metadataPrefix': 'oai_dc'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertEqual(resp.count('<record>'), 1)
        self.assertIn('<datestamp>2014-02-04</datestamp>', resp)

    def test_list_records_with_set(self):
        request = testing.DummyRequest()
        request.registry.settings = settings
        request.db = settings['db_conn']
        request.params = {'verb': 'ListRecords', 'set': 'bla-x-ble', 'metadataPrefix': 'oai_dc'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertEqual(resp.count('<record>'), 1)
        self.assertIn('<setSpec>bla-x-ble</setSpec>', resp)

    def test_any_verb_return_id_not_exist_if_inexistent_id(self):
        request = testing.DummyRequest()
        request.registry.settings = settings
        request.db = settings['db_conn']
        request.params = {'verb': 'GetRecord', 'identifier': 'bla', 'metadataPrefix': 'oai_dc'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<error code="idDoesNotExist">No matching identifier</error>', resp)

    def test_any_verb_return_no_record_match_if_search_returns_empty(self):
        request = testing.DummyRequest()
        request.registry.settings = settings
        request.db = settings['db_conn']
        request.params = {'verb': 'ListRecords', 'from': '2014-02-07', 'until': '2014-02-08', 'metadataPrefix': 'oai_dc'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<error code="noRecordsMatch"/>', resp)

    def test_identify_verb_return_bad_argument_if_invalid_argument(self):
        request = testing.DummyRequest()
        request.registry.settings = settings
        request.db = settings['db_conn']
        request.params = {'verb': 'Identify', 'x': 'a'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<error code="badArgument"/>', resp)

    def test_list_metadata_formats_verb_return_bad_argument_if_invalid_argument(self):
        request = testing.DummyRequest()
        request.registry.settings = settings
        request.db = settings['db_conn']
        request.params = {'verb': 'ListMetadataFormats', 'x': 'a'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<error code="badArgument"/>', resp)

    def test_list_metadata_formats_verb_with_identifier_returns_success(self):
        request = testing.DummyRequest()
        request.registry.settings = settings
        request.db = settings['db_conn']
        request.params = {'verb': 'ListMetadataFormats', 'identifier': '38t'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<metadataPrefix>oai_dc</metadataPrefix>', resp)

    def test_list_identifiers_verb_return_bad_argument_if_invalid_argument(self):
        request = testing.DummyRequest()
        request.registry.settings = settings
        request.db = settings['db_conn']
        request.params = {'verb': 'ListIdentifiers', 'x': 'a'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<error code="badArgument"/>', resp)

    def test_list_identifiers_verb_return_bad_argument_without_metadata_prefix(self):
        request = testing.DummyRequest()
        request.registry.settings = settings
        request.db = settings['db_conn']
        request.params = {'verb': 'ListIdentifiers'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<error code="badArgument"/>', resp)

    def test_list_identifiers_verb_return_success_with_metadata_prefix(self):
        request = testing.DummyRequest()
        request.registry.settings = settings
        request.db = settings['db_conn']
        request.params = {'verb': 'ListIdentifiers', 'metadataPrefix': 'oai_dc'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<setSpec>edufba</setSpec>', resp)

    def test_list_sets_verb_return_bad_argument_if_invalid_argument(self):
        request = testing.DummyRequest()
        request.registry.settings = settings
        request.db = settings['db_conn']
        request.params = {'verb': 'ListSets', 'x': 'a'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<error code="badArgument"/>', resp)

    def test_list_sets_verb_return_success_without_invalid_argument(self):
        request = testing.DummyRequest()
        request.registry.settings = settings
        request.db = settings['db_conn']
        request.params = {'verb': 'ListSets'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<setSpec>edufba</setSpec>', resp)

    def test_get_record_verb_return_bad_argument_if_invalid_argument(self):
        request = testing.DummyRequest()
        request.db = settings['db_conn']
        request.params = {'verb': 'GetRecord', 'x': 'a'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<error code="badArgument"/>', resp)

    def test_get_record_verb_return_bad_argument_without_metadata_prefix(self):
        request = testing.DummyRequest()
        request.db = settings['db_conn']
        request.params = {'verb': 'GetRecord', 'identifier': '38t'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<error code="badArgument"/>', resp)

    def test_get_record_verb_return_bad_argument_without_identifier(self):
        request = testing.DummyRequest()
        request.db = settings['db_conn']
        request.params = {'verb': 'GetRecord', 'metadataPrefix': 'oai_dc'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<error code="badArgument"/>', resp)

    def test_list_records_verb_return_bad_argument_if_invalid_argument(self):
        request = testing.DummyRequest()
        request.db = settings['db_conn']
        request.params = {'verb': 'ListRecords', 'x': 'a'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<error code="badArgument"/>', resp)

    def test_list_records_verb_return_bad_argument_without_metadata_prefix(self):
        request = testing.DummyRequest()
        request.db = settings['db_conn']
        request.params = {'verb': 'ListRecords'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<error code="badArgument"/>', resp)

    def test_any_verb_return_bad_argument_if_cant_parse_dates(self):
        request = testing.DummyRequest()
        request.db = settings['db_conn']
        request.params = {'verb': 'ListRecords', 'from': '2014-0207', 'metadataPrefix': 'oai_dc'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<error code="badArgument"/>', resp)

    def test_any_verb_return_cannot_diss_format_if_metadata_prefix_is_not_oai_dc(self):
        request = testing.DummyRequest()
        request.db = settings['db_conn']
        request.params = {'verb': 'ListRecords', 'metadataPrefix': 'oai_marc'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<error code="cannotDisseminateFormat"/>', resp)

    def test_filter_books_raise_exception_when_unsupported_metadataformat(self):
        request_params = {'metadataPrefix': 'oai_marc'}
        self.assertRaises(oaipmh.CannotDisseminateFormatError, filter_books, 
            request_params, settings['db_conn'], settings)

    def test_filter_books_raise_exception_when_inexistent_id(self):
        request_params = {'identifier': '72t'}
        self.assertRaises(oaipmh.IDDoesNotExistError, filter_books, request_params, 
            settings['db_conn'], settings)

    def test_filter_books_raise_exception_when_no_books_find(self):
        request_params = {'set':'teste'}
        self.assertRaises(oaipmh.NoRecordsMatchError, filter_books, 
            request_params, settings['db_conn'], settings)
    
    def test_filter_books_raise_exception_when_invalid_data_format(self):
        request_params = {'from':'20140310'}
        self.assertRaises(ValueError, filter_books, request_params, settings['db_conn'], settings)

    def test_filter_books_return_books_if_ok(self):
        request_params = {'identifier': '38t', 'metadataPrefix': 'oai_dc'}
        books = filter_books(request_params, settings['db_conn'], settings)
        self.assertEqual(books.next()['identifier'], '38t')

    def test_deleted_register_show_only_header_info(self):
        request = testing.DummyRequest()
        request.db = settings['db_conn']
        request.params = {'verb': 'GetRecord', 'metadataPrefix': 'oai_dc', 'identifier': '37t'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<header status="deleted">', resp)
        self.assertNotIn('<metadata>', resp)

    def test_resumption_token_limit_results(self):
        request = testing.DummyRequest()
        request.registry.settings = settings
        request.db = settings['db_conn']
        request.params = {'verb': 'ListRecords', 'metadataPrefix': 'oai_dc'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertEqual(resp.count('<record>'), 2)
        self.assertIn('36t', resp)
        self.assertIn('37t', resp)

    def test_resumption_token_paginate_results(self):
        request = testing.DummyRequest()
        request.registry.settings = settings
        request.db = settings['db_conn']
        request.params = {'verb': 'ListRecords', 'metadataPrefix': 'oai_dc', 'resumptionToken': '1'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertEqual(resp.count('<record>'), 2)
        self.assertIn('38t', resp)
        self.assertIn('39t', resp)

    def test_resumption_token_show_last_page(self):
        request = testing.DummyRequest()
        request.registry.settings = settings
        request.db = settings['db_conn']
        request.params = {'verb': 'ListRecords', 'metadataPrefix': 'oai_dc', 'resumptionToken': '2'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertEqual(resp.count('<record>'), 1)
        self.assertIn('40t', resp)

    def test_any_verb_returns_bad_resumption_token_with_invalid_resumption_token(self):
        request = testing.DummyRequest()
        request.registry.settings = settings
        request.db = settings['db_conn']
        request.params = {'verb': 'ListRecords', 'metadataPrefix': 'oai_dc', 'resumptionToken': '3'}
        resp = oai_pmh(request)
        resp = str(resp)
        self.assertIn('<error code="badResumptionToken"/>', resp)
        
