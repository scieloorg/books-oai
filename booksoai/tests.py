import unittest
from datetime import datetime, date

from pyramid import testing
from pyramid.httpexceptions import HTTPNotFound

from .utils import get_db_connection
from .sync import mark_as_deleted
from .sync import get_updates, update_from_api, adapt_data

from porteira.porteira import Schema
from mock import patch, call


settings = {}
settings['mongo_uri'] = 'mongodb://localhost:27017/scielobooks-test'
settings['scielo_uri'] = 'http://books.scielo.org/api/v1/'


def tearDownModule():
    db = get_db_connection(settings)
    db.connection.drop_database(db.name)


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


class SyncTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.db = get_db_connection(settings)
        
    def tearDown(self):
        testing.tearDown()

    @patch('booksoai.sync.get_data_from_api')
    def test_get_updates_no_updates_return_empty_list(self, mock_data):
        mock_data.return_value = {'results': [], 'last_seq':0}
 
        resp = get_updates(settings)
        update = self.db.updates.find_one()
        
        self.assertEquals(resp, [])
        self.assertEquals(update['last_seq'], 0)

    @patch('booksoai.sync.get_data_from_api')
    def test_get_updates_with_updates_return_updates_list(self, mock_data):
        mock_data.return_value = {'results': [{'seq': 2}], 'last_seq': 2}
 
        resp = get_updates(settings)
        update = self.db.updates.find_one()

        self.assertEquals(resp, [{'seq': 2}])
        self.assertEquals(update['last_seq'], 2)

    @patch('booksoai.sync.get_data_from_api')
    def test_get_updates_with_previous_updates_return_only_new_updates(self, mock_data):
        self.db.updates.remove()
        self.db.updates.insert({'last_seq': 2}, w=1)
        mock_data.return_value = {'results': [], 'last_seq': 3}

        get_updates(settings)
        
        api_data_call = call('%s_changes?since=%s' % (settings['scielo_uri'], 2))
        self.assertEquals(mock_data.call_args_list, [api_data_call])

    @patch('booksoai.sync.get_data_from_api')
    @patch('booksoai.sync.get_updates')
    def test_update_from_api_return_none_if_no_updates(self, mock_update, mock_data):
        mock_update.return_value = []

        resp = update_from_api(settings)

        self.assertEquals(resp, None)
        self.assertEquals(mock_data.call_count, 0)

    @patch('booksoai.sync.datetime')
    @patch('booksoai.sync.persists_data')
    @patch('booksoai.sync.get_data_from_api')
    @patch('booksoai.sync.get_updates')
    def test_update_from_api_with_updates(self, mock_update, mock_api_data, mock_persists, mock_datetime):
        test_datetime = datetime(2014, 01, 31, 0, 0)
        mock_datetime.now.return_value = test_datetime
        mock_update.return_value = [{'id':1, 'changes':[{'rev': '2'}]}]
        mock_api_data.return_value = {'_id':10, 'publisher': 'teste'}

        update_from_api(settings)

        uri = '%s%s/' % (settings['scielo_uri'], 1)
        api_data_call = call(uri, {'rev':'2'})
        persists_call = call({'datestamp': test_datetime, 'identifier':10, 'publisher': 'teste'}, settings)

        self.assertEquals(mock_api_data.call_args_list, [api_data_call])
        self.assertEquals(mock_persists.call_args_list, [persists_call])

    @patch('booksoai.sync.mark_as_deleted')
    @patch('booksoai.sync.get_updates')
    def test_update_from_api_with_deletions(self, mock_update, mock_mark_as_deleted):
        mock_update.return_value = [{'a':1, 'b':2, 'deleted':True}]

        update_from_api(settings)

        mock_call = call({'a':1, 'b':2, 'deleted':True}, settings)
        self.assertEquals(mock_mark_as_deleted.call_args_list, [mock_call])

    @patch('booksoai.sync.datetime')
    def test_adapt_data_ignore_non_mapped_fields(self, mock_datetime):
        test_datetime = datetime(2014, 01, 31, 0, 0)
        mock_datetime.now.return_value = test_datetime
        data = {
            'a':1, 'b':2, 'c':3, '_id':4
        }
        adapted = adapt_data(data)

        self.assertEquals(adapted, {'datestamp': test_datetime, 'identifier':4})

    @patch('booksoai.sync.datetime')
    def test_adapt_data_handle_default_value_fields(self, mock_datetime):
        test_datetime = datetime(2014, 01, 31, 0, 0)
        mock_datetime.now.return_value = test_datetime
        data = {
            '_id':4, 'pdf_file': {'x':1}, 'epub_file': 'x' 
        }
        adapted = adapt_data(data)

        self.assertEquals(adapted, {'datestamp': test_datetime, 'identifier':4, 'formats': ['pdf', 'epub']})

    @patch('booksoai.sync.datetime')
    def test_mark_as_deleted_update_register(self, mock_datetime):
        test_datetime = datetime(2014, 01, 31, 0, 0)
        mock_datetime.now.return_value = test_datetime
        book = {'identifier':1}
        
        db = get_db_connection(settings)
        db.books.insert(book)

        update = {'id':1, 'deleted': True}
        mark_as_deleted(update, settings)

        book = db.books.find_one({'identifier': 1})
        self.assertEquals(book['deleted'], True)
        self.assertEquals(book['datestamp'], test_datetime)

