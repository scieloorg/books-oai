import logging
import requests

from datetime import datetime
from multiprocessing import Process
from requests.exceptions import HTTPError, ConnectionError

from .utils import get_db_connection


logging.basicConfig()
logger = logging.getLogger('Sync')

FIELD_MAP = (
    ('publisher', 'publisher'),
    ('_id', 'identifier'),
    ('language', 'language'),
    ('synopsis', 'description'),
    ('year', 'date'),
    ('title', 'title'),
    ('updated', 'updated'),
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
                if _from == 'updated':
                    adapted[to] = data[_from][0:10]
                else:
                    adapted[to] = data[_from]
    return adapted


def mark_as_deleted(update, db):
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


def persists_data(data, db):
    db.books.update({
        'identifier': data['identifier']
    }, {
        '$set': data
    }, upsert=True)
    logger.info('Saved book. ID: %s' % data['identifier'])


def get_data_from_api(uri, revision=None):
    req = requests.get(uri, params=revision)
    req.raise_for_status()
    data = req.json()
    return data


def get_updates(api_uri, db):
    update = db.updates.find_one()
    last_change = update['last_seq'] if update else 0

    changes_uri = '%s/changes/?since=%s' % (api_uri, last_change)
    data = get_data_from_api(changes_uri)

    return data['results']


def update_last_seq(db, seq):
    db.updates.update({
        '_id': 1
    }, {
        '$set': {
            'last_seq': seq,
            'updated_at': datetime.now()
        }
    }, upsert=True)


def update_from_api(settings):
    try:
        db = get_db_connection(settings)
        api_uri = settings.get('scielo_uri')
        updates = get_updates(api_uri, db)

        for update in updates:
            if update.get('deleted'):
                mark_as_deleted(update, db)
            else:
                revision = update['changes'][-1]
                uri = '%s/book/%s/' % (api_uri, update['id'])

                try:
                    data = get_data_from_api(uri, revision)
                except HTTPError as e:
                    logger.error('[ID %s] %s' % (update['id'], e.message))
                    continue

                adapted = adapt_data(data)
                persists_data(adapted, db)
                update_last_seq(db, update['seq'])

    except (HTTPError, ConnectionError) as e:
        logger.exception('%s: %s' % (e.__class__.__name__, e.message))

    except Exception as e:
        logger.exception('%s' % e.message)


def do_sync(settings):
    process = Process(target=update_from_api, args=[settings])
    process.daemon = True
    process.start()
