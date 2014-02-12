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
        data = {'verb': 'Identifier', 'baseURL': 'http://books.scielo.org/oai/'}
        xml = etree.Element('root')
        
        pipe = pipeline.RequestPipe()
        resp_xml, resp_data = pipe.transform((xml, data))

        xml_str = '<root><request verb="Identifier">http://books.scielo.org/oai/</request></root>'

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


class TestHeaderPipe(unittest.TestCase):

    def test_header_pipe_add_header_with_three_subelements(self):
        data = {
            'identifier': 'xpto',
            'datestamp': datetime(2014, 02, 12, 10, 55, 00),
            'publisher': 'Teste OAI-PMH'
        }

        pipe = pipeline.HeaderPipe()
        xml = pipe.transform(data)

        xml_str = '<header>'
        xml_str += '<identifier>xpto</identifier>'
        xml_str += '<datestamp>2014-02-12</datestamp>'
        xml_str += '<setSpec>teste-oai-pmh</setSpec>'
        xml_str += '</header>'

        self.assertEqual(etree.tostring(xml), xml_str)


class TestListIdentifiersPipe(unittest.TestCase):

    def test_list_identifiers_add_one_header_for_each_identifier(self):
        data = {
            'verb': 'ListIdentifiers',
            'baseURL': 'http://books.scielo.org/oai/',
            'books': [
                {
                    'identifier': 'xpto',
                    'datestamp': datetime(2014, 02, 12, 10, 55, 00),
                    'publisher': 'Teste OAI-PMH'
                }, {
                    'identifier': 'xvzp',
                    'datestamp': datetime(2014, 01, 27, 10, 55, 00),
                    'publisher': 'OAI-PMH SciELO'
                }
            ]
        }
        root = etree.Element('root')

        pipe = pipeline.ListIdentifiersPipe()
        xml, data = pipe.transform((root, data))

        xml_str = '<root>'
        xml_str += '<ListIdentifiers>'
        xml_str += '<header>'
        xml_str += '<identifier>xpto</identifier>'
        xml_str += '<datestamp>2014-02-12</datestamp>'
        xml_str += '<setSpec>teste-oai-pmh</setSpec>'
        xml_str += '</header>'
        xml_str += '<header>'
        xml_str += '<identifier>xvzp</identifier>'
        xml_str += '<datestamp>2014-01-27</datestamp>'
        xml_str += '<setSpec>oai-pmh-scielo</setSpec>'
        xml_str += '</header>'
        xml_str += '</ListIdentifiers>'
        xml_str += '</root>'

        self.assertEqual(etree.tostring(xml), xml_str)


class TestSetPipe(unittest.TestCase):

    def test_set_pipe_add_set_with_two_subelements(self):
        data = {
            'publisher': 'Editora UNESP',
        }

        pipe = pipeline.SetPipe()
        xml = pipe.transform(data)

        xml_str = '<set>'
        xml_str += '<setSpec>editora-unesp</setSpec>'
        xml_str += '<setName>Editora UNESP</setName>'
        xml_str += '</set>'

        self.assertEqual(etree.tostring(xml), xml_str)


class TestListSetsPipe(unittest.TestCase):

    def test_list_sets_add_one_set_for_each_publisher(self):
        data = {
            'verb': 'ListIdentifiers',
            'baseURL': 'http://books.scielo.org/oai/',
            'books': [
                {
                    'publisher': 'Teste OAI-PMH'
                }, {
                    'publisher': 'OAI-PMH SciELO'
                }
            ]
        }
        root = etree.Element('root')

        pipe = pipeline.ListSetsPipe()
        xml, data = pipe.transform((root, data))

        xml_str = '<root>'
        xml_str += '<ListSets>'
        xml_str += '<set>'
        xml_str += '<setSpec>teste-oai-pmh</setSpec>'
        xml_str += '<setName>Teste OAI-PMH</setName>'
        xml_str += '</set>'
        xml_str += '<set>'
        xml_str += '<setSpec>oai-pmh-scielo</setSpec>'
        xml_str += '<setName>OAI-PMH SciELO</setName>'
        xml_str += '</set>'
        xml_str += '</ListSets>'
        xml_str += '</root>'

        self.assertEqual(etree.tostring(xml), xml_str)