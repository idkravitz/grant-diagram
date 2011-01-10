import sqlite3
import logging
import os, os.path

from grant_core.init_tables import tables, Table
from grant_core.CountHours import CountHours

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
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.create_aggregate('count_hours', 2, CountHours)

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

    def select(self, table, fields, where=None, group_by=None, **kwargs):
        template = "select {1} from {0}"
        if 'joins' in kwargs:
            fromclause = ""
            for j in kwargs['joins']:
                fromclause += " inner join {0} on {1}={2}".format(*j)
            table += fromclause
        query = template.format(table, ",".join(fields))

        if where: query += " where {0}".format(where)
        if group_by: query += " group by {0}".format(",".join(group_by))
        self._log(query)
        cursor = self.connection.cursor()
        if 'values' in kwargs and len(kwargs['values']):
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

    def delete(self, table, pkey, pkeyval):
        base = "delete from {0}".format(table)
        where = " and ".join("{0}=?".format(p) for p in pkey)
        query = base  + " where " + where
        self._log(query)
        cursor = self.connection.cursor()
        cursor.execute(query, pkeyval)
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

    def get_fk_values(self, field, exclude=None):
        verbose = field.verbose_field
        where = exclude and '{0}!={1}'.format(field.fk.name, exclude)
        return self.db.select(field.fk.table.name, (field.fk.name, verbose.name), where).fetchall()

    def get_prj_fk_for_manager(self, username):
        where = 'id in (select project_id from developers_distribution where developer_username=?)'
        return self.db.select('projects', ('id', 'name'), where, values=(username,)).fetchall()

    def get_tasks_fk_for_manager(self, username):
        return self.db.select('tasks as a', ('a.id', 'a.title'),
            'b.developer_username=? and b.is_manager=1',
            joins=(('developers_distribution as b', 'a.project_id', 'b.project_id'),),
            values=(username,)).fetchall()

    def get_tasks_projects_id(self):
        return self.db.select('tasks', ('project_id',)).fetchall()

    def get_tasks_dependencies_projects_id(self):
        return self.db.select('tasks_dependencies as b', ('a.project_id',), joins=(("tasks as a", "b.task_id", "a.id"),)).fetchall()

    def update_record(self, tablename, values, pk):
        fields = [f.name for f in Table.tables[tablename] if not (f.hidden and f.pk)]
        pkey = [p.name for p in Table.tables[tablename].pk]
        return self.db.update(tablename, fields, values, pkey, pk)

    def add_record(self, tablename, values):
        fields = [f.name for f in Table.tables[tablename] if not (f.hidden and f.pk)]
        pairs = dict(zip(fields, values))
        return self.db.insert(tablename, **pairs)

    def delete_record(self, tablename, pk):
        pkeys = [p.name for p in Table.tables[tablename].pk]
        return self.db.delete(tablename, pkeys, pk)

    def get_available_developers(self, project_id):
        where = 'company_id in (select company_id from contracts where status="active" and project_id=?) or company_id=1'
        return self.db.select('developers', ('username', 'username'), where, values=(project_id,)).fetchall()

    def get_available_tasks(self, task_id):
        project_id, = self.db.select('tasks', ('project_id',), 'id=?',
            values=(task_id,)).fetchone()
        return self.get_available_tasks_for_project(project_id)

    def get_available_tasks_for_project(self, project_id):
        return self.db.select('tasks', ('id', 'title'), 'project_id=?', values=(project_id,)).fetchall()

    def get_available_tasks_dependencies(self, task_id):
        project_id, = self.db.select('tasks', ('project_id',), 'id=?',
            values=(task_id,)).fetchone()
        return self.db.select('tasks_dependencies as a', ('a.task_id', 'a.depended_task_id'),
            'b.project_id=?',
            joins=(('tasks as b', 'a.task_id', 'b.id'),),
            values=(project_id,)).fetchall()

    def get_developers_tasks(self, username):
        return self.db.select('tasks as a',
            ('a.id', 'a.title'),
            joins=(('developers_distribution as b', 'a.project_id', 'b.project_id'),),
            where="b.developer_username=?", values=(username,)).fetchall()


    def get_table(self, tablename):
        table = Table.tables[tablename]
        joins, fields = [], []
        pseudonames = (chr(ch) for ch in range(ord('a'), ord('z')))      # joined tables name mangling
        pkfields = [f.fullname() for f in table.pk]
        for f in table.fields:
            if f.fk:
                pseudoname = next(pseudonames)
                fields.append(f.verbose_field.fullname(pseudoname))
                jtable = f.fk.table.name
                joins.append(("{0} as {1}".format(jtable, pseudoname),
                    f.fullname(),
                    f.fk.fullname(pseudoname)))
            elif not f.hidden:
                fields.append(f.fullname())
        return self.db.select(tablename, pkfields + fields, joins=joins).fetchall()

    def get_managed_projects(self, username):
        return self.db.select('developers_distribution', ('project_id',),
            'developer_username=? and is_manager=1', values=(username,)).fetchall()

    def get_record(self, tablename, pkeys):
        table = Table.tables[tablename]
        where_clause = " and ".join("{0}=?".format(f.name) for f in table.pk)
        return self.db.select(tablename, ('*',), where_clause, values=pkeys).fetchone()

    def add_company(self, name):
        self.db.insert('companies', name=name)

    def get_companies(self):
        return self.db.select('companies', ('*',)).fetchall()

    def countReportsForDateTimeSice(self, begin_date, end_date, username, exclude):
        where = "developer_username = ?3 and ((end_date <= ?2 and end_date > ?1) or (begin_date >= ?1 and begin_date < ?2) or \
(begin_date <= ?1 and end_date >= ?2))"
        values = (begin_date, end_date, username)
        if exclude is not None:
            where += " and id <> ?"
            values = values + exclude
        return self.db.select('reports', ('count(*)',), where=where, values=values).fetchone()[0]

    def check_company_name_is_free(self, name):
        count = self.db.select('companies', ('count(*)',), 'name=?', values=(name,)).fetchone()
        return not count[0]

    def check_username_is_free(self, username):
        count = self.db.select('developers', ('count(*)',), 'username=?', values=(username,)).fetchone()
        return not count[0]

    def add_first_admin(self, username, password, fullname, company):
        self.add_company(company)
        self.add_developer(username, password, fullname, company, True)

    def add_developer(self, username, password, fullname, company, is_admin):
        if type(company) is str:
            cursor = self.db.select('companies', ('id',), 'name=?', values=(company,))
            company = cursor.fetchone()[0]
        self.db.insert('developers', username=username, password=password, full_name=fullname, company_id=company, is_admin=is_admin)

    def get_user(self, username, password):
        cur = self.db.select('developers', ('is_admin',), 'username=? and password=?', values=(username,password))
        res = cur.fetchone()
        return res and res[0]

    def has_admins(self, username=None):
        where = 'is_admin=1'
        kwargs = {}
        if username is not None:
            where += ' and username!=?'
            kwargs['values'] = (username,)
        admins_count = self.db.select('developers', ('count(*)',), where, **kwargs)
        res = admins_count.fetchone()[0]
        return res

    def has_companies(self):
        companies_count = self.db.select('companies', ('count(*)',))
        return companies_count.fetchone()[0]

    def get_activities_report(self, project_id=None, developer_username=None, task_id=None):
        where = []
        values = []
        if project_id is not None:
            where.append('c.id=?')
            values.append(project_id)
        if developer_username is not None:
            where.append('a.developer_username=?')
            values.append(developer_username)
        if task_id is not None:
            where.append('a.task_id=?')
            values.append(task_id)
        if len(where) == 0:
            where = None
        else:
            where = " and ".join(where)
        joins = ('tasks as b', 'a.task_id', 'b.id'), ('projects as c', 'b.project_id', 'c.id')
        return self.db.select('reports as a',
            ('c.name', 'a.developer_username', 'b.title', 'count_hours(a.begin_date, a.end_date)'),
            where=where,
            joins=joins,
            values=values,
            group_by=('b.project_id', 'a.developer_username', 'a.task_id')).fetchall()

    def has_distributed(self, username):
        count = self.db.select('developers_distribution', ('count(*)',), 'developer_username=?',
            values=(username,)).fetchone()
        return count[0] != 0

    def get_distributed_developers(self):
        return self.db.select('developers_distribution', ('developer_username', 'developer_username'),
            group_by=('developer_username',)).fetchall()
