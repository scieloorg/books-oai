from lxml import etree


xmlns = "http://www.openarchives.org/OAI/2.0/"
xsi = "http://www.w3.org/2001/XMLSchema-instance"
schemaLocation = "http://www.openarchives.org/OAI/2.0/"
schemaLocation += "http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"
attrib = {"{%s}schemaLocation" % xsi: schemaLocation}

def make_xml(data):
    root = etree.Element("OAI-PMH", nsmap={None:xmlns, 'xsi':xsi}, attrib=attrib)
    for k, v in data.items():
        sub = etree.SubElement(root, k)
        if not isinstance(v, dict):
            sub.text = str(v)
        else:
            for kk, vv in v.items():
                etree.SubElement(sub, kk).text = str(vv)
    return root


def oai_factory(info):
    
    def _render(value, system):
        request = system.get('request')
        if request is not None:
            response = request.response
            response.charset = 'utf-8'
            response.content_type = 'application/xml'
        return etree.tostring(make_xml(value), pretty_print=True)
    return _render

