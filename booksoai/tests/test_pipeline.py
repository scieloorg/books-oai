import unittest
from datetime import datetime

from lxml import etree
from mock import patch

from booksoai import pipeline


class TestSetupPipe(unittest.TestCase):

    def test_setup_add_root_xml_element(self):
        data = {}
        pipe = pipeline.SetupPipe()
        resp_xml, resp_data = pipe.transform(data)

        xml_str = '<OAI-PMH xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        xml_str += ' xmlns="http://www.openarchives.org/OAI/2.0/"'
        xml_str += ' xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/'
        xml_str += ' http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"></OAI-PMH>'
        xml_root = etree.fromstring(xml_str)
        
        self.assertEqual(etree.tostring(xml_root), etree.tostring(resp_xml))
        self.assertEqual(resp_data, data)


class TestResponseDatePipe(unittest.TestCase):

    @patch('booksoai.pipeline.datetime')
    def test_response_date_add_datetime_in_response(self, mock_utc):
        mock_utc.utcnow.return_value = datetime(2014, 02, 06, 15, 17, 00)
        data = {}
        xml = etree.Element('root')
        
        pipe = pipeline.ResponseDatePipe()
        resp_xml, resp_data = pipe.transform((xml, data))

        xml_str = '<root><responseDate>2014-02-06T15:17:00Z</responseDate></root>'

        self.assertEqual(etree.tostring(resp_xml), xml_str)


class TestRequestPipe(unittest.TestCase):

    def test_request_add_verb_and_base_url(self):
        data = {'verb': 'Identifyer', 'baseURL': 'http://books.scielo.org/oai/'}
        xml = etree.Element('root')
        
        pipe = pipeline.RequestPipe()
        resp_xml, resp_data = pipe.transform((xml, data))

        xml_str = '<root><request verb="Identifyer">http://books.scielo.org/oai/</request></root>'

        self.assertEqual(etree.tostring(resp_xml), xml_str)


class TestIdentifyNodePipe(unittest.TestCase):

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
        
        pipe = pipeline.IdentifyNodePipe()
        resp_xml, resp_data = pipe.transform((xml, data))

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

    def test_teardown_returns_only_xml(self):
        data = {}
        xml = etree.Element('root')
        
        pipe = pipeline.TearDownPipe()
        resp_xml = pipe.transform((xml, data))

        self.assertEqual(etree.tostring(resp_xml), etree.tostring(xml))


class TestListMetadataFormatsPipe(unittest.TestCase):

    def test_list_metadata_add_node_to_root_element(self):
        data = {}
        xml = etree.Element('root')

        pipe = pipeline.ListMetadataFormatsPipe()
        resp_xml, resp_data = pipe.transform((xml, data))

        xml_str = '<root><ListMetadataFormats/></root>'
        self.assertEqual(etree.tostring(resp_xml), xml_str)


class TestMetadataFormatPipe(unittest.TestCase):

    def test_metadata_format_add_info_to_root_element(self):
        data = {
            'formats': [
                {
                    'prefix': 'prefix',
                    'schema': 'schema',
                    'namespace': 'namespace'
                }, {
                    'prefix': 'prefix2',
                    'schema': 'schema2',
                    'namespace': 'namespace2'
                }
            ]
        }
        xml = etree.Element('root')
        etree.SubElement(xml, 'ListMetadataFormats')
        
        pipe = pipeline.MetadataFormatPipe()
        resp_xml, resp_data = pipe.transform((xml, data))

        xml_str = '<root>'
        xml_str += '<ListMetadataFormats>'
        xml_str += '<metadataFormat>'
        xml_str += '<metadataPrefix>prefix</metadataPrefix>'
        xml_str += '<schema>schema</schema>'
        xml_str += '<metadataNamespace>namespace</metadataNamespace>'
        xml_str += '</metadataFormat>'
        xml_str += '<metadataFormat>'
        xml_str += '<metadataPrefix>prefix2</metadataPrefix>'
        xml_str += '<schema>schema2</schema>'
        xml_str += '<metadataNamespace>namespace2</metadataNamespace>'
        xml_str += '</metadataFormat>'
        xml_str += '</ListMetadataFormats>'
        xml_str += '</root>'

        self.assertEqual(etree.tostring(resp_xml), xml_str)
