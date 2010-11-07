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
fk = lambda t, table, column="id": "{0} references {1} ({2}) on delete cascade on update cascade".format(t, table, column)

tables = OrderedDict([
    ("companies", OrderedDict(
        [
            ("id", pk("integer")),
            ("name", "text")
        ])
    ),
    ("projects", OrderedDict(
        [
            ("id", pk("integer")),
            ("begin_date", "integer not null"),
            ("end_date", "integer not null")
        ])
    ),
    ("developers", OrderedDict(
        [
            ("full_name", "text"),
            ("username", pk("text")),
            ("company_id", fk("integer", "companies")),
            ("password", "text"),
            ("is_admin", "integer")
        ])
    ),
    ("developers_distribution", OrderedDict(
        [
            ("developer_username", fk("text", "developers", "username")),
            ("project_id", fk("integer", "projects")),
            ("constraint developers_distribution_pk", "primary key(developer_username, project_id)")
        ])
    ),
    ("tasks", OrderedDict(
        [
            ("id", pk("integer")),
            ("title", "text"),
            ("description", "text"),
            ("project_id", fk("integer", "projects")),
            ("hours", "integer"),
            ("status", "integer")
        ])
    ),
    ("tasks_dependencies", OrderedDict(
        [
            ("task_id", fk("integer", "tasks")),
            ("depended_task_id", fk("integer", "tasks"))
        ])
    ),
    ("contracts", OrderedDict(
        [
            ("number", pk("integer")),
            ("company_id", fk("integer", "companies")),
            ("project_id", fk("integer", "projects")),
            ("date_of_creation", "integer"),
            ("status", "integer")
        ])
    ),
    ("reports", OrderedDict(
        [
            ("id", pk("integer")),
            ("developer_id", fk("integer", "developers", "username")),
            ("task_id", fk("integer", "tasks")),
            ("begin_date", "integer"),
            ("end_date", "integer"),
            ("description", "text")
        ])
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
