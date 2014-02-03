

def parse_to_xml(data):
    pass

def oai_factory(info):
    
    def _render(value, system):
        request = system.get('request')
        if request is not None:
            response = request.response
            response.charset = 'utf-8'
            response.content_type = 'application/xml'
        return parse_to_xml(value)
    return _render

