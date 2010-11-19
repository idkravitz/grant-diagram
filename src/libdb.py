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
            connection.commit()
            return connection

        self.echo = echo
        self.connection = connect()

    def insert(self, table, **vals):
        template = "insert into {0} ({1}) values ({2})"
        fields = ",".join(field for field in vals)
        mask = ",".join(['?'] * len(vals))
        self.connection.execute(template.format(table, fields, mask), tuple(vals.values()))
        self.connection.commit()

    def select(self, table, fields, where=None, **kwargs):
        template = "select {1} from {0}"
        if where: template += " where {2}"
        query = template.format(table, ",".join(fields), where)
        print(query)
        cursor = self.connection.cursor()
        if 'values' in kwargs:
            cursor.execute(query, kwargs['values'])
        else:
            cursor.execute(query)
        return cursor

    def _log(self, msg):
        if self.echo:
            self.logger.debug(msg)

class Grant(object):
    def __init__(self, **kwargs):
        if 'db' in kwargs:
            self.db = kwargs['db']
        else:
            self.db = Database(**kwargs)

    def add_company(self, name):
        self.db.insert('companies', name=name)

    def add_developer(self, fullname, username, company, password, is_admin):
        cursor = self.db.select('companies', ('id',), 'name=?', values=(company,))
        print(cursor.fetchall())

