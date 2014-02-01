import logging
import requests

from datetime import datetime
from multiprocessing import Process
from requests.exceptions import HTTPError, ConnectionError

from .utils import get_db_connection


logger = logging.getLogger('Sync')

FIELD_MAP = (
    ('publisher', 'publisher'),
    ('_id', 'identifier'),
    ('language', 'language'),
    ('synopsis', 'description'),
    ('year', 'date'),
    ('title', 'title'),
    ('creators', 'creators'),
    ('pdf_file', ('formats', 'pdf')),
    ('epub_file', ('formats', 'epub'))
)

def adapt_data(data):
    """
    Adapt data from books API to OAI-PHM proposal.

    It uses 'FIELD_MAP' (from/to tuples) to ignore don't needed fields and 
    adapt keys. If the 'to' element of 'FIELD_MAP' was a tuple, it uses the
    second value as a default value.

    :param data: Data from books API.
    :type data: dict.
    :returns:  dict.
    """
    adapted = {'datestamp': datetime.now()}
    for _from, to in FIELD_MAP:
        if _from in data:
            if isinstance(to, tuple):
                to, value = to
                adapted.setdefault(to, []).append(value)
            else:
                adapted[to] = data[_from]
    return adapted


def mark_as_deleted(update, settings):
    db = get_db_connection(settings)
    _id = update['id']
    db.books.update({
        'identifier': _id
    }, {
        '$set': {
            'deleted': True,
            'datestamp': datetime.now()
        }
    })
    logger.info('Mark book as deleted. ID: %s' % update['id'])


def persists_data(data, settings):
    db = get_db_connection(settings)
    db.books.update({
        'identifier': data['identifier']
    }, {
        '$set': data
    }, upsert=True)
    logger.info('Saved book. ID: %s' % data['identifier'])


def get_data_from_api(uri, revision=None):
    req = requests.get(uri, params=revision)
    data = req.json()
    return data


def get_updates(settings):
    db = get_db_connection(settings)
    update = db.updates.find_one()
    last_change = update['last_seq'] if update else 0

    api_uri = settings.get('scielo_uri')
    changes_uri = '%s_changes?since=%s' % (api_uri, last_change)
    data = get_data_from_api(changes_uri)

    db.updates.update({
        '_id': 1
    }, {
        '$set': {
            'last_seq': data['last_seq'],
            'updated_at': datetime.now()
        }
    }, upsert=True)
    return data['results']


def update_from_api(settings):
    try:
        updates = get_updates(settings)
        api_uri = settings.get('scielo_uri')
        
        for update in updates:
            if update.get('deleted'):
                mark_as_deleted(update, settings)
            else:
                revision = update['changes'][-1]
                uri = '%s%s/' % (api_uri, update['id'])
                data = get_data_from_api(uri, revision)
                adapted = adapt_data(data)
                persists_data(adapted, settings)

    except (HTTPError, ConnectionError) as e:
        logger.error('%s: %s' % (e.__class__.__name__, e.message))

    except Exception as e:
        logger.error('%s' % e.message)


def do_sync(settings):
    process = Process(target=update_from_api, args=[settings])
    process.start()
    process.join()