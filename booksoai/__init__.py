# coding: utf-8
import os
import pymongo
import logging

from datetime import datetime, timedelta

from pyramid.events import NewRequest, NewResponse
from pyramid.config import Configurator

from .sync import do_sync
from .utils import get_db_connection


DEFAULT_SETTINGS = [
        ('mongo_uri', 'BOOKSOAI_MONGO_URI', str,
            'mongodb://localhost:27017/scielobooks_oai'),
        ('scielo_uri', 'BOOKSOAI_SCIELO_URI', str,
            'http://books.scielo.org/api/v1'),
        ('auto_sync', 'BOOKSOAI_AUTO_SYNC', bool,
            True),
        ('auto_sync_interval', 'BOOKSOAI_AUTO_SYNC_INTERVAL', int,
            60*60*12),
        ('items_per_page', 'BOOKSOAI_ITEMS_PER_PAGE', int,
            100),
        ]


def parse_settings(settings):
    """Analisa e retorna as configurações da app com base no arquivo .ini e env.

    As variáveis de ambiente possuem precedência em relação aos valores
    definidos no arquivo .ini.
    """
    parsed = {}
    cfg = list(DEFAULT_SETTINGS)

    for name, envkey, convert, default in cfg:
        value = os.environ.get(envkey, settings.get(name, default))
        if convert is not None:
            value = convert(value)
        parsed[name] = value

    return parsed


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=parse_settings(settings))
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('oai_pmh', '/oai-pmh')
    config.add_renderer('oai', factory='booksoai.renderers.oai_factory')

    # Starts sync process on new requests
    def start_sync(event):
        settings = event.request.registry.settings
        if settings['auto_sync']:
            db = event.request.db
            interval = settings['auto_sync_interval']
            try:
                update = db.updates.find_one()
                if update:
                    last_update = update['updated_at']
                    next_update = last_update + timedelta(seconds=interval)
                    if next_update < datetime.now():
                        do_sync(settings)
                else:
                    do_sync(settings)
            except pymongo.errors.AutoReconnect as e:
                logging.getLogger(__name__).error('MongoDB: %s' % e.message)


    def create_db_conn(event):
        settings = event.request.registry.settings
        db = get_db_connection(settings)
        event.request.db = db

    def close_db_conn(event):
        try:
            event.request.db.connection.close()
        except TypeError:
            pass
     
    config.add_subscriber(create_db_conn, NewRequest)
    config.add_subscriber(close_db_conn, NewResponse)
    config.add_subscriber(start_sync, NewRequest)
    config.scan(ignore='booksoai.tests')
    return config.make_wsgi_app()
