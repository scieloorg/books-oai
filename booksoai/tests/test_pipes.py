import unittest
from datetime import datetime

from lxml import etree
from mock import patch
from pyramid import testing

from booksoai import pipeline


class TestSetupPipe(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        
    def tearDown(self):
        testing.tearDown()

    def test_setup_add_root_xml_element(self):
        data = {}
        setup = pipeline.SetupPipe()
        resp_xml, resp_data = setup.transform(data)

        xml_str = '<OAI-PMH xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        xml_str += ' xmlns="http://www.openarchives.org/OAI/2.0/"'
        xml_str += ' xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/'
        xml_str += ' http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"></OAI-PMH>'
        xml_root = etree.fromstring(xml_str)
        
        self.assertEqual(etree.tostring(xml_root), etree.tostring(resp_xml))
        self.assertEqual(resp_data, data)


class TestResponseDatePipe(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        
    def tearDown(self):
        testing.tearDown()

    @patch('booksoai.pipeline.datetime')
    def test_response_date_add_datetime_in_response(self, mock_utc):
        mock_utc.utcnow.return_value = datetime(2014, 02, 06, 15, 17, 00)
        data = {}
        xml = etree.Element('root')
        
        setup = pipeline.ResponseDatePipe()
        resp_xml, resp_data = setup.transform((xml, data))

        xml_str = '<root><responseDate>2014-02-06T15:17:00Z</responseDate></root>'

        self.assertEqual(etree.tostring(resp_xml), xml_str)


class TestRequestPipe(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        
    def tearDown(self):
        testing.tearDown()

    def test_request_add_verb_and_base_url(self):
        data = {'verb': 'Identifyer', 'baseURL': 'http://books.scielo.org/oai/'}
        xml = etree.Element('root')
        
        setup = pipeline.RequestPipe()
        resp_xml, resp_data = setup.transform((xml, data))

        xml_str = '<root><request verb="Identifyer">http://books.scielo.org/oai/</request></root>'

        self.assertEqual(etree.tostring(resp_xml), xml_str)


class TestIdentifyNodePipe(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        
    def tearDown(self):
        testing.tearDown()

    def test_identify_node_add_identity_info(self):
        data = {
            'repositoryName': 'SciELO Books',
            'baseURL': 'http://books.scielo.org/oai/',
            'protocolVersion': '2.0',
            'adminEmail': 'books@scielo.org',
            'earliestDatestamp': datetime(1909, 04, 01),
            'deletedRecord': 'persistent',
            'granularity': 'YYYY-MM-DD'
        }
        xml = etree.Element('root')
        
        setup = pipeline.IdentifyNodePipe()
        resp_xml, resp_data = setup.transform((xml, data))

        xml_str = '<root>'
        xml_str += '<Identify>'
        xml_str += '<repositoryName>SciELO Books</repositoryName>'
        xml_str += '<baseURL>http://books.scielo.org/oai/</baseURL>'
        xml_str += '<protocolVersion>2.0</protocolVersion>'
        xml_str += '<adminEmail>books@scielo.org</adminEmail>'
        xml_str += '<earliestDatestamp>1909-04-01</earliestDatestamp>'
        xml_str += '<deletedRecord>persistent</deletedRecord>'
        xml_str += '<granularity>YYYY-MM-DD</granularity>'
        xml_str += '</Identify>'
        xml_str += '</root>'

        self.assertEqual(etree.tostring(resp_xml), xml_str)


class TestTearDownPipe(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        
    def tearDown(self):
        testing.tearDown()

    def test_teardown_returns_only_xml(self):
        data = {}
        xml = etree.Element('root')
        
        setup = pipeline.TearDownPipe()
        resp_xml = setup.transform((xml, data))

        self.assertEqual(etree.tostring(resp_xml), etree.tostring(xml))
