from pyramid.config import Configurator


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('oai_pmh', '/oai-pmh')
    config.scan()
    config.add_renderer('oai', factory='booksoai.renderers.oai_factory')
    return config.make_wsgi_app()
