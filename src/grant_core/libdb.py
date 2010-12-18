import sqlite3
import logging
import os, os.path

from grant_core.init_tables import tables, Table

# Add logger, connect it with file handler

class Database(object):
    logger = logging.getLogger('libdb')
    logger.setLevel(logging.DEBUG)
    ch = logging.FileHandler('Database.log', mode="w")
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(ch)

    def __init__(self, echo=False, dbname=':memory:'):
        self.dbname = dbname
        self.echo = echo
        self.connection = self._connect()

    def _connect(self):
        self._log('-- connecting {0} database'.format(self.dbname))
        connection = sqlite3.connect(self.dbname) if os.path.isfile(self.dbname) else self._init_database()
        return connection

    def _init_database(self):
        self._log('-- starting init process for "{0}" database'.format(self.dbname))
        connection = sqlite3.connect(self.dbname)
        for t in tables:
            query = str(t)
            self._log(query)
            connection.execute(query)
        self._log('-- database "{0}" created'.format(self.dbname))
        connection.commit()
        return connection

    def insert(self, table, **vals):
        template = "insert into {0} ({1}) values ({2})"
        fields = ",".join(field for field in vals)
        mask = ",".join(['?'] * len(vals))
        self.connection.execute(template.format(table, fields, mask), tuple(vals.values()))
        self.connection.commit()

    def select(self, table, fields, where=None, **kwargs):
        template = "select {1} from {0}"
        if 'joins' in kwargs:
            fromclause = ""
            for j in kwargs['joins']:
                fromclause = " inner join {0} on {1}={2}".format(*j)
            table += fromclause
        query = template.format(table, ",".join(fields))

        if where: query += " where {0}".format(where)
        self._log(query)
        cursor = self.connection.cursor()
        if 'values' in kwargs:
            cursor.execute(query, kwargs['values'])
        else:
            cursor.execute(query)
        return cursor

    def update(self, table, fields, values, pkey, pkeyval):
        base = "update {0} set ".format(table)
        set_ = ",".join("{0}=?".format(f) for f in fields)
        where = " and ".join("{0}=?".format(p) for p in pkey)
        query = base + set_ + " where " + where
        self._log(query)
        cursor = self.connection.cursor()
        cursor.execute(query, values + pkeyval)
        self.connection.commit()
        return cursor

    def clear(self):
        self.connection.close()
        if self.dbname != ":memory:":
            os.unlink(self.dbname)
        self.connection = self._init_database()

    def _log(self, msg):
        if self.echo:
            self.logger.debug(msg)

class Grant(object):
    def __init__(self, **kwargs):
        if 'db' in kwargs:
            self.db = kwargs['db']
        else:
            self.db = Database(**kwargs)

    def get_headers(self, tablename=None, table=None):
        table = table or Table.tables[tablename]
        headers = []
        for f in table.fields:
            if f.fk:
                headers += self.get_headers(table=f.fk.table)
            elif not f.hidden:
                    headers.append((f.name, type(f)))
        return headers

    def get_fields_description(self, tablename):
        return Table.tables[tablename].fields

    def get_fk_values(self, field):
        verboses = field.verbose_fields
        return self.db.select(field.fk.table.name, [field.fk.name] + [f.name for f in verboses]).fetchall()

    def update_record(self, tablename, values, pk):
        fields = [f.name for f in Table.tables[tablename].fields if not f.hidden or f.fk]
        pkey = [p.name for p in Table.tables[tablename].pk]
        return self.db.update(tablename, fields, values, pkey, pk)

    def add_record(self, tablename, values):
        fields = [f.name for f in Table.tables[tablename].fields if not f.hidden or f.fk]
        pairs = dict(zip(fields, values))
        return self.db.insert(tablename, **pairs)

    def get_table(self, tablename):
        def extract_fields(table):
            fields = []
            joins = []
            for f in table.fields:
                if f.fk:
                    res = extract_fields(f.fk.table)
                    joins.append((f.fk.table.name, f.fullname(), f.fk.fullname()))
                    fields += res[0]
                    joins += res[1]
                elif not f.hidden:
                    fields.append("{0}.{1}".format(table.name, f.name))
            return fields, joins

        if tablename in Table.tables:
            table = Table.tables[tablename]
            pk = table.pk
            pkfields = ["{0}.{1}".format(tablename, f.name) for f in pk]
            fields, joins = extract_fields(table)
            return self.db.select(tablename, pkfields + fields, joins=joins).fetchall()

    def get_record(self, tablename, pkeys):
        table = Table.tables[tablename]
        where_clause = ",".join("{0}=?".format(f.name) for f in table.pk)
        return self.db.select(tablename, ('*',), where_clause, values=pkeys).fetchone()

    def add_company(self, name):
        self.db.insert('companies', name=name)

    def add_first_admin(self, username, password, fullname, company):
        self.add_company(company)
        self.add_developer(username, password, fullname, company, True)

    def get_companies(self):
        return self.db.select('companies', ('*',)).fetchall()

    def add_developer(self, username, password, fullname, company, is_admin):
        if type(company) is str:
            cursor = self.db.select('companies', ('id',), 'name=?', values=(company,))
            company = cursor.fetchone()[0]
        self.db.insert('developers', username=username, password=password, full_name=fullname, company_id=company, is_admin=is_admin)

    def get_user(self, username, password):
        cur = self.db.select('developers', ('is_admin',), 'username=? and password=?', values=(username,password))
        res = cur.fetchone()
        return res and res[0]

    def has_admins(self):
        admins_count = self.db.select('developers', ('count(*)',), 'is_admin=1')
        return admins_count.fetchone()[0]

    def has_companies(self):
        companies_count = self.db.select('companies', ('count(*)',))
        return companies_count.fetchone()[0]
