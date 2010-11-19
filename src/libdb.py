import sqlite3
import logging
import os.path

from init_tables import tables

# Add logger, connect it with file handler

class Database(object):
    logger = logging.getLogger('libdb')
    logger.setLevel(logging.DEBUG)
    ch = logging.FileHandler('Database.log', mode="w")
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(ch)

    def __init__(self, echo=False, dbname='test'):

        def connect():
            self._log('-- connecting {0} database'.format(dbname))
            connection = sqlite3.connect(dbname) if os.path.isfile(dbname) else init_database()
            return connection

        def init_database():
            self._log('-- starting init process for "{0}" database'.format(dbname))
            connection = sqlite3.connect(dbname)
            for name, fields in tables.items():
                query = "create table {0} (\n{1}\n);".format(
                    name,
                    ",\n".join(" " * 4 + " ".join(col for col in field if col) for field in fields.items()))
                self._log(query)
                connection.execute(query)
            self._log('-- database "{0}" created'.format(dbname))
            return connection

        self.echo = echo
        self.connection = connect()

    def _log(self, msg):
        if self.echo:
            self.logger.debug(msg)

class Grant(object):
    def __init__(self, **kwargs):
        if 'db' in kwargs:
            self.db = kwargs['db']
        else:
            self.db = Database(**kwargs)

