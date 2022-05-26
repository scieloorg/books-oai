import unittest
from datetime import datetime
from pyramid.registry import Registry

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
        data = {
            'baseURL': 'http://books.scielo.org/oai/',
            'request': {'verb': 'Identifier'}
        }
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
        root = etree.Element('root')
        pipe = pipeline.HeaderPipe()
        xml, data = pipe.transform((root, data))

        xml_str = '<root>'
        xml_str += '<header>'
        xml_str += '<identifier>xpto</identifier>'
        xml_str += '<datestamp>2014-02-12</datestamp>'
        xml_str += '<setSpec>teste-oai-pmh</setSpec>'
        xml_str += '</header>'
        xml_str += '</root>'

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
        data = 'Editora UNESP'

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
            'books': ['Teste OAI-PMH', 'OAI-PMH SciELO']
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


class TestMetadataPipe(unittest.TestCase):

    def test_metadata_pipe_add_record_as_dublin_core(self):
        data = {
            'title': 'title',
            'creators': {
                'collaborator': [['collaborator', None]],
                'organizer': [['organizer', None]]
            },
            'description': 'description',
            'publisher': 'publisher',
            'date': '2014',
            'formats': ['pdf', 'epub'],
            'identifier': 'identifier',
            'language': 'pt'
        }
        root = etree.Element('root')

        pipe = pipeline.MetadataPipe()
        xml, data = pipe.transform((root, data))

        xml_str = '<root>'
        xml_str += '<metadata>'
        xml_str += '<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"'
        xml_str += ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        xml_str += ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
        xml_str += ' xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/'
        xml_str += ' http://www.openarchives.org/OAI/2.0/oai_dc.xsd">'
        xml_str += '<dc:title>title</dc:title>'
        xml_str += '<dc:creator>organizer</dc:creator>'
        xml_str += '<dc:contributor>collaborator</dc:contributor>'
        xml_str += '<dc:description>description</dc:description>'
        xml_str += '<dc:publisher>publisher</dc:publisher>'
        xml_str += '<dc:date>2014</dc:date>'
        xml_str += '<dc:type>book</dc:type>'
        xml_str += '<dc:format>pdf</dc:format>'
        xml_str += '<dc:format>epub</dc:format>'
        xml_str += '<dc:identifier>http://books.scielo.org/id/identifier</dc:identifier>'
        xml_str += '<dc:language>pt</dc:language>'
        xml_str += '</oai_dc:dc>'
        xml_str += '</metadata>'
        xml_str += '</root>'

        self.assertEqual(etree.tostring(xml), xml_str)

    def test_metadata_pipe_add_record_as_dublin_core_with_individual_author(self):
        data = {
            'title': 'title',
            'creators': {
                'individual_author': [
                    ['individual_author1', None], 
                    ['individual_author2', None]
                ],
            },
            'description': 'description',
            'publisher': 'publisher',
            'date': '2014',
            'formats': ['pdf', 'epub'],
            'identifier': 'identifier',
            'language': 'pt'
        }
        root = etree.Element('root')

        pipe = pipeline.MetadataPipe()
        xml, data = pipe.transform((root, data))

        xml_str = '<root>'
        xml_str += '<metadata>'
        xml_str += '<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"'
        xml_str += ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        xml_str += ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
        xml_str += ' xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/'
        xml_str += ' http://www.openarchives.org/OAI/2.0/oai_dc.xsd">'
        xml_str += '<dc:title>title</dc:title>'
        xml_str += '<dc:creator>individual_author1</dc:creator>'
        xml_str += '<dc:creator>individual_author2</dc:creator>'
        xml_str += '<dc:description>description</dc:description>'
        xml_str += '<dc:publisher>publisher</dc:publisher>'
        xml_str += '<dc:date>2014</dc:date>'
        xml_str += '<dc:type>book</dc:type>'
        xml_str += '<dc:format>pdf</dc:format>'
        xml_str += '<dc:format>epub</dc:format>'
        xml_str += '<dc:identifier>http://books.scielo.org/id/identifier</dc:identifier>'
        xml_str += '<dc:language>pt</dc:language>'
        xml_str += '</oai_dc:dc>'
        xml_str += '</metadata>'
        xml_str += '</root>'

        self.assertEqual(etree.tostring(xml), xml_str)

    def test_metadata_pipe_add_record_as_dublin_core_with_corporate_author(self):
        data = {
            'title': 'title',
            'creators': {
                'corporate_author': [
                    ['corporate_author1', None], 
                    ['corporate_author2', None], 
                    ['corporate_author3', None]
                ],
            },
            'description': 'description',
            'publisher': 'publisher',
            'date': '2014',
            'formats': ['pdf', 'epub'],
            'identifier': 'identifier',
            'language': 'pt'
        }
        root = etree.Element('root')

        pipe = pipeline.MetadataPipe()
        xml, data = pipe.transform((root, data))

        xml_str = '<root>'
        xml_str += '<metadata>'
        xml_str += '<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"'
        xml_str += ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        xml_str += ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
        xml_str += ' xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/'
        xml_str += ' http://www.openarchives.org/OAI/2.0/oai_dc.xsd">'
        xml_str += '<dc:title>title</dc:title>'
        xml_str += '<dc:creator>corporate_author1</dc:creator>'
        xml_str += '<dc:creator>corporate_author2</dc:creator>'
        xml_str += '<dc:creator>corporate_author3</dc:creator>'
        xml_str += '<dc:description>description</dc:description>'
        xml_str += '<dc:publisher>publisher</dc:publisher>'
        xml_str += '<dc:date>2014</dc:date>'
        xml_str += '<dc:type>book</dc:type>'
        xml_str += '<dc:format>pdf</dc:format>'
        xml_str += '<dc:format>epub</dc:format>'
        xml_str += '<dc:identifier>http://books.scielo.org/id/identifier</dc:identifier>'
        xml_str += '<dc:language>pt</dc:language>'
        xml_str += '</oai_dc:dc>'
        xml_str += '</metadata>'
        xml_str += '</root>'

        self.assertEqual(etree.tostring(xml), xml_str)


    def test_metadata_pipe_add_record_as_dublin_core_with_organizer(self):
        data = {
            'title': 'title',
            'creators': {
                'organizer': [
                    ['organizer1', None], 
                    ['organizer2', None], 
                ],
            },
            'description': 'description',
            'publisher': 'publisher',
            'date': '2014',
            'formats': ['pdf', 'epub'],
            'identifier': 'identifier',
            'language': 'pt'
        }
        root = etree.Element('root')

        pipe = pipeline.MetadataPipe()
        xml, data = pipe.transform((root, data))

        xml_str = '<root>'
        xml_str += '<metadata>'
        xml_str += '<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"'
        xml_str += ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        xml_str += ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
        xml_str += ' xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/'
        xml_str += ' http://www.openarchives.org/OAI/2.0/oai_dc.xsd">'
        xml_str += '<dc:title>title</dc:title>'
        xml_str += '<dc:creator>organizer1</dc:creator>'
        xml_str += '<dc:creator>organizer2</dc:creator>'
        xml_str += '<dc:description>description</dc:description>'
        xml_str += '<dc:publisher>publisher</dc:publisher>'
        xml_str += '<dc:date>2014</dc:date>'
        xml_str += '<dc:type>book</dc:type>'
        xml_str += '<dc:format>pdf</dc:format>'
        xml_str += '<dc:format>epub</dc:format>'
        xml_str += '<dc:identifier>http://books.scielo.org/id/identifier</dc:identifier>'
        xml_str += '<dc:language>pt</dc:language>'
        xml_str += '</oai_dc:dc>'
        xml_str += '</metadata>'
        xml_str += '</root>'

        self.assertEqual(etree.tostring(xml), xml_str)

    def test_metadata_pipe_add_record_as_dublin_core_with_multiple_author_groups(self):
        data = {
            'title': 'title',
            'creators': {
                'individual_author': [
                    ['individual_author1', None], 
                    ['individual_author2', None]
                ],
                'corporate_author': [
                    ['corporate_author1', None], 
                    ['corporate_author2', None], 
                    ['corporate_author3', None]
                ],
                'organizer': [
                    ['organizer1', None], 
                    ['organizer2', None], 
                ],
            },
            'description': 'description',
            'publisher': 'publisher',
            'date': '2014',
            'formats': ['pdf', 'epub'],
            'identifier': 'identifier',
            'language': 'pt'
        }
        root = etree.Element('root')

        pipe = pipeline.MetadataPipe()
        xml, data = pipe.transform((root, data))

        xml_str = '<root>'
        xml_str += '<metadata>'
        xml_str += '<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"'
        xml_str += ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        xml_str += ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
        xml_str += ' xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/'
        xml_str += ' http://www.openarchives.org/OAI/2.0/oai_dc.xsd">'
        xml_str += '<dc:title>title</dc:title>'
        xml_str += '<dc:creator>individual_author1</dc:creator>'
        xml_str += '<dc:creator>individual_author2</dc:creator>'
        xml_str += '<dc:creator>corporate_author1</dc:creator>'
        xml_str += '<dc:creator>corporate_author2</dc:creator>'
        xml_str += '<dc:creator>corporate_author3</dc:creator>'
        xml_str += '<dc:creator>organizer1</dc:creator>'
        xml_str += '<dc:creator>organizer2</dc:creator>'
        xml_str += '<dc:description>description</dc:description>'
        xml_str += '<dc:publisher>publisher</dc:publisher>'
        xml_str += '<dc:date>2014</dc:date>'
        xml_str += '<dc:type>book</dc:type>'
        xml_str += '<dc:format>pdf</dc:format>'
        xml_str += '<dc:format>epub</dc:format>'
        xml_str += '<dc:identifier>http://books.scielo.org/id/identifier</dc:identifier>'
        xml_str += '<dc:language>pt</dc:language>'
        xml_str += '</oai_dc:dc>'
        xml_str += '</metadata>'
        xml_str += '</root>'

        self.assertEqual(etree.tostring(xml), xml_str)

    def test_metadata_pipe_add_record_as_dublin_core_with_translator_contributor(self):
        data = {
            'title': 'title',
            'creators': {
                'translator': [
                    ['translator1', None], 
                    ['translator2', None]
                ],
            },
            'description': 'description',
            'publisher': 'publisher',
            'date': '2014',
            'formats': ['pdf', 'epub'],
            'identifier': 'identifier',
            'language': 'pt'
        }
        root = etree.Element('root')

        pipe = pipeline.MetadataPipe()
        xml, data = pipe.transform((root, data))

        xml_str = '<root>'
        xml_str += '<metadata>'
        xml_str += '<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"'
        xml_str += ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        xml_str += ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
        xml_str += ' xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/'
        xml_str += ' http://www.openarchives.org/OAI/2.0/oai_dc.xsd">'
        xml_str += '<dc:title>title</dc:title>'
        xml_str += '<dc:contributor>translator1</dc:contributor>'
        xml_str += '<dc:contributor>translator2</dc:contributor>'
        xml_str += '<dc:description>description</dc:description>'
        xml_str += '<dc:publisher>publisher</dc:publisher>'
        xml_str += '<dc:date>2014</dc:date>'
        xml_str += '<dc:type>book</dc:type>'
        xml_str += '<dc:format>pdf</dc:format>'
        xml_str += '<dc:format>epub</dc:format>'
        xml_str += '<dc:identifier>http://books.scielo.org/id/identifier</dc:identifier>'
        xml_str += '<dc:language>pt</dc:language>'
        xml_str += '</oai_dc:dc>'
        xml_str += '</metadata>'
        xml_str += '</root>'

        self.assertEqual(etree.tostring(xml), xml_str)

    def test_metadata_pipe_add_record_as_dublin_core_with_editor_contributor(self):
        data = {
            'title': 'title',
            'creators': {
                'editor': [
                    ['editor1', None], 
                ],
            },
            'description': 'description',
            'publisher': 'publisher',
            'date': '2014',
            'formats': ['pdf', 'epub'],
            'identifier': 'identifier',
            'language': 'pt'
        }
        root = etree.Element('root')

        pipe = pipeline.MetadataPipe()
        xml, data = pipe.transform((root, data))

        xml_str = '<root>'
        xml_str += '<metadata>'
        xml_str += '<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"'
        xml_str += ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        xml_str += ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
        xml_str += ' xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/'
        xml_str += ' http://www.openarchives.org/OAI/2.0/oai_dc.xsd">'
        xml_str += '<dc:title>title</dc:title>'
        xml_str += '<dc:contributor>editor1</dc:contributor>'
        xml_str += '<dc:description>description</dc:description>'
        xml_str += '<dc:publisher>publisher</dc:publisher>'
        xml_str += '<dc:date>2014</dc:date>'
        xml_str += '<dc:type>book</dc:type>'
        xml_str += '<dc:format>pdf</dc:format>'
        xml_str += '<dc:format>epub</dc:format>'
        xml_str += '<dc:identifier>http://books.scielo.org/id/identifier</dc:identifier>'
        xml_str += '<dc:language>pt</dc:language>'
        xml_str += '</oai_dc:dc>'
        xml_str += '</metadata>'
        xml_str += '</root>'

        self.assertEqual(etree.tostring(xml), xml_str)
class TestRecordPipe(unittest.TestCase):

    def test_record_pipe_add_record_node(self):
        data = {
            'datestamp': datetime(2014, 02, 19, 13, 05, 00),
            'title': 'title',
            'creators': {
                'collaborator': [['collaborator', None]],
                'organizer': [['organizer', None]]
            },
            'description': 'description',
            'publisher': 'publisher',
            'date': '2014',
            'formats': ['pdf', 'epub'],
            'identifier': 'identifier',
            'language': 'pt'
        }

        pipe = pipeline.RecordPipe()
        xml = pipe.transform(data)

        xml_str = '<record>'
        xml_str += '<header>'
        xml_str += '<identifier>identifier</identifier>'
        xml_str += '<datestamp>2014-02-19</datestamp>'
        xml_str += '<setSpec>publisher</setSpec>'
        xml_str += '</header>'
        xml_str += '<metadata>'
        xml_str += '<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"'
        xml_str += ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        xml_str += ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
        xml_str += ' xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/'
        xml_str += ' http://www.openarchives.org/OAI/2.0/oai_dc.xsd">'
        xml_str += '<dc:title>title</dc:title>'
        xml_str += '<dc:creator>organizer</dc:creator>'
        xml_str += '<dc:contributor>collaborator</dc:contributor>'
        xml_str += '<dc:description>description</dc:description>'
        xml_str += '<dc:publisher>publisher</dc:publisher>'
        xml_str += '<dc:date>2014</dc:date>'
        xml_str += '<dc:type>book</dc:type>'
        xml_str += '<dc:format>pdf</dc:format>'
        xml_str += '<dc:format>epub</dc:format>'
        xml_str += '<dc:identifier>http://books.scielo.org/id/identifier</dc:identifier>'
        xml_str += '<dc:language>pt</dc:language>'
        xml_str += '</oai_dc:dc>'
        xml_str += '</metadata>'
        xml_str += '</record>'

        self.assertEqual(etree.tostring(xml), xml_str)


class TestGetRecordPipe(unittest.TestCase):

    def test_get_record_pipe_add_get_record(self):
        data = {
            'verb': 'GetRecord',
            'baseURL': 'http://books.scielo.org/oai/',
            'books': [{
                'datestamp': datetime(2014, 02, 19, 13, 05, 00),
                'title': 'title',
                'creators': {
                    'collaborator': [['collaborator', None]],
                    'organizer': [['organizer', None]]
                },
                'description': 'description',
                'publisher': 'publisher',
                'date': '2014',
                'formats': ['pdf', 'epub'],
                'identifier': 'identifier',
                'language': 'pt'
            }]
        }

        root = etree.Element('root')
        pipe = pipeline.GetRecordPipe()
        xml, data = pipe.transform((root, data))

        xml_str = '<root>'
        xml_str += '<GetRecord>'
        xml_str += '<record>'
        xml_str += '<header>'
        xml_str += '<identifier>identifier</identifier>'
        xml_str += '<datestamp>2014-02-19</datestamp>'
        xml_str += '<setSpec>publisher</setSpec>'
        xml_str += '</header>'
        xml_str += '<metadata>'
        xml_str += '<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"'
        xml_str += ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        xml_str += ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
        xml_str += ' xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/'
        xml_str += ' http://www.openarchives.org/OAI/2.0/oai_dc.xsd">'
        xml_str += '<dc:title>title</dc:title>'
        xml_str += '<dc:creator>organizer</dc:creator>'
        xml_str += '<dc:contributor>collaborator</dc:contributor>'
        xml_str += '<dc:description>description</dc:description>'
        xml_str += '<dc:publisher>publisher</dc:publisher>'
        xml_str += '<dc:date>2014</dc:date>'
        xml_str += '<dc:type>book</dc:type>'
        xml_str += '<dc:format>pdf</dc:format>'
        xml_str += '<dc:format>epub</dc:format>'
        xml_str += '<dc:identifier>http://books.scielo.org/id/identifier</dc:identifier>'
        xml_str += '<dc:language>pt</dc:language>'
        xml_str += '</oai_dc:dc>'
        xml_str += '</metadata>'
        xml_str += '</record>'
        xml_str += '</GetRecord>'
        xml_str += '</root>'

        self.assertEqual(etree.tostring(xml), xml_str)


class TestListRecordsPipe(unittest.TestCase):

    def test_list_records_pipe_add_many_records_node(self):
        data = {
            'verb': 'ListRecords',
            'baseURL': 'http://books.scielo.org/oai/',
            'books': [{
                'datestamp': datetime(2014, 02, 19, 13, 05, 00),
                'title': 'title',
                'creators': {
                    'collaborator': [['collaborator', None]],
                    'organizer': [['organizer', None]]
                },
                'description': 'description',
                'publisher': 'publisher',
                'date': '2014',
                'formats': ['pdf', 'epub'],
                'identifier': 'identifier',
                'language': 'pt'
            }]
        }

        root = etree.Element('root')
        pipe = pipeline.ListRecordsPipe()
        xml, data = pipe.transform((root, data))

        xml_str = '<root>'
        xml_str += '<ListRecords>'
        xml_str += '<record>'
        xml_str += '<header>'
        xml_str += '<identifier>identifier</identifier>'
        xml_str += '<datestamp>2014-02-19</datestamp>'
        xml_str += '<setSpec>publisher</setSpec>'
        xml_str += '</header>'
        xml_str += '<metadata>'
        xml_str += '<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"'
        xml_str += ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        xml_str += ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
        xml_str += ' xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/'
        xml_str += ' http://www.openarchives.org/OAI/2.0/oai_dc.xsd">'
        xml_str += '<dc:title>title</dc:title>'
        xml_str += '<dc:creator>organizer</dc:creator>'
        xml_str += '<dc:contributor>collaborator</dc:contributor>'
        xml_str += '<dc:description>description</dc:description>'
        xml_str += '<dc:publisher>publisher</dc:publisher>'
        xml_str += '<dc:date>2014</dc:date>'
        xml_str += '<dc:type>book</dc:type>'
        xml_str += '<dc:format>pdf</dc:format>'
        xml_str += '<dc:format>epub</dc:format>'
        xml_str += '<dc:identifier>http://books.scielo.org/id/identifier</dc:identifier>'
        xml_str += '<dc:language>pt</dc:language>'
        xml_str += '</oai_dc:dc>'
        xml_str += '</metadata>'
        xml_str += '</record>'
        xml_str += '</ListRecords>'
        xml_str += '</root>'

        self.assertEqual(etree.tostring(xml), xml_str)


class TestResumptionTokenPipe(unittest.TestCase):
    
    @patch.object(Registry, 'settings')
    def test_resumption_token_add_next_token_if_not_finished(self, mock_settings):
        mock_settings.return_value = {'items_per_page': '2'}
        data = {
            'books': [{}, {}],
            'request': {}
        }
        root = etree.Element('root')

        pipe = pipeline.ResumptionTokenPipe()
        xml, data = pipe.transform((root, data))

        xml_str = '<root>'
        xml_str += '<resumptionToken>1</resumptionToken>'
        xml_str += '</root>'

        self.assertEqual(etree.tostring(xml), xml_str)

    @patch.object(Registry, 'settings')
    def test_resumption_token_empty_if_finished(self, mock_settings):
        mock_settings.return_value = {'items_per_page': '2'}
        data = {
            'books': [{}, {}],
            'request': {'resumptionToken': '1'}
        }
        root = etree.Element('root')

        pipe = pipeline.ResumptionTokenPipe()
        xml, data = pipe.transform((root, data))

        xml_str = '<root>'
        xml_str += '<resumptionToken/>'
        xml_str += '</root>'

        self.assertEqual(etree.tostring(xml), xml_str)