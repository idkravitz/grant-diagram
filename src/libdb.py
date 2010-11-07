import sqlite3
import logging
import os.path

from collections import OrderedDict

# Add logger, connect it with file handler
logger = logging.getLogger('libdb')
logger.setLevel(logging.DEBUG)

ch = logging.FileHandler('libdb.log', mode="w")
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter("%(message)s"))

logger.addHandler(ch)

def connect_database(db_name):
    logger.debug('-- connecting {0} database'.format(db_name))
    connection = sqlite3.connect(db_name) if os.path.isfile(db_name) else init_database(db_name)

pk = lambda t: "{0} primary key".format(t)

tables = OrderedDict([
    ("companies",
        {
            "id": pk("integer"),
            "name": "text"
        }
    ),
    ("projects",
        {
            "id": pk("integer"),
            "begin_date": "integer not null",
            "end_date": "integer not null"
        }
    ),
    ('developers',
        {
            "full_name": "text",
            "username": pk("text"),
            "password": "text",
            "is_admin": "integer"
        }
    ),
    ('tasks',
        {
            "id": pk("integer"),
            "title": "text",
            "description": "text",
            "hours": "integer",
            "status": "integer"
        }
    ),
    ('contracts',
        {
            "number": pk("integer"),
            "date_of_creation": "integer",
            "status": "integer"
        }
    ),
    ('reports',
        {
            "id": pk("integer"),
            "begin_date": "integer",
            "end_date": "integer",
            "description": "text"
        }
    ),
])

def init_database(db_name):
    logger.debug('-- starting init process for {0} database'.format(db_name))
    connection = sqlite3.connect(db_name)
    for name, fields in tables.items():
        query = "create table {0} (\n{1}\n);".format(
            name,
            ",\n".join(" " * 4 + " ".join(field) for field in fields.items()))
        logger.debug(query)
        connection.execute(query)
    return connection
