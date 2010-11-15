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
    return connection

def pk(t):
    return "{0} primary key".format(t)

def fk(t, table, column="id"):
    return "{0} references {1} ({2}) on delete cascade on update cascade".format(t, table, column)

def nn(t):
    return "{0} not null".format(t)

def unique(t):
    return "{0} unique".format(t)


def constraint(name="", body=None):
    left_side = ""
    if name:
        left_side = "constraint " + name
    return (left_side, body)

def check_bool(field):
    return constraint(
        name=("bool_" + field),
        body="check ({0} in (0,1))".format(field))

def date_precendance(before, after):
    return constraint(
        name="date_precendace_{0}_and_{1}".format(before, after),
        body="check ({0} < {1})".format(before, after))

def check_date(field):
    return constraint(
        name="date_"+field,
        body="check ({0} > 0)".format(field))

def constraint_pk(*fields):
    return constraint(body="primary key ({0})".format(",".join(fields)))

def check_enum(field, *values):
    return constraint(name="enum_"+field,
        body="check ({0} in ({1}))".format(field, ",".join('"{0}"'.format(v) for v in values)))

tables = OrderedDict([
    ("companies", OrderedDict(
        [
            ("id", pk("integer")),
            ("name", unique(nn("text")))
        ])
    ),
    ("projects", OrderedDict(
        [
            ("id", pk("integer")),
            ("begin_date", nn("integer")),
            ("end_date", nn("integer")),
            date_precendance("begin_date", "end_date"),
            check_date("begin_date")
        ])
    ),
    ("developers", OrderedDict(
        [
            ("full_name", nn("text")),
            ("username", pk("text")),
            ("company_id", nn(fk("integer", "companies"))),
            ("password", nn("text")),
            ("is_admin", nn("integer")),
            check_bool("is_admin")
        ])
    ),
    ("developers_distribution", OrderedDict(
        [
            ("developer_username", nn(fk("text", "developers", "username"))),
            ("project_id", nn(fk("integer", "projects"))),
            ("is_manager", nn("integer")),
            constraint_pk("developer_username", "project_id"),
            check_bool("is_manager")
        ])
    ),
    ("tasks", OrderedDict(
        [
            ("id", pk("integer")),
            ("title", nn("text")),
            ("description", nn("text")),
            ("project_id", nn(fk("integer", "projects"))),
            ("hours", nn("integer")),
            ("status", nn("integer")),
            check_enum("status", "active", "finished", "delayed")
        ])
    ),
    ("tasks_dependencies", OrderedDict(
        [
            ("task_id", nn(fk("integer", "tasks"))),
            ("depended_task_id", nn(fk("integer", "tasks"))),
            constraint_pk("task_id", "depended_task_id")
        ])
    ),
    ("contracts", OrderedDict(
        [
            ("number", pk("integer")),
            ("company_id", nn(fk("integer", "companies"))),
            ("project_id", nn(fk("integer", "projects"))),
            ("date_of_creation", nn("integer")),
            ("status", nn("integer")),
            check_date("date_of_creation"),
            check_enum("status", "active", "finished", "delayed")
        ])
    ),
    ("reports", OrderedDict(
        [
            ("id", pk("integer")),
            ("developer_id", nn(fk("integer", "developers", "username"))),
            ("task_id", nn(fk("integer", "tasks"))),
            ("begin_date", nn("integer")),
            ("end_date", nn("integer")),
            ("description", nn("text")),
            date_precendance("begin_date", "end_date"),
            check_date("begin_date")
        ])
    ),
])

def init_database(db_name):
    logger.debug('-- starting init process for {0} database'.format(db_name))
    connection = sqlite3.connect(db_name)
    for name, fields in tables.items():
        query = "create table {0} (\n{1}\n);".format(
            name,
            ",\n".join(" " * 4 + " ".join(col for col in field if col) for field in fields.items()))
        logger.debug(query)
        connection.execute(query)
    return connection
