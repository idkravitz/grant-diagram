__ALL__ = ("tables")

class Table(object):
    tables = {}
    def __init__(self, name, *fields, **options):
        self.name = name
        self.fields = fields
        self.constraints = []
        if "pk" in options:
            self.pk = [f for f in fields if f.name in options["pk"]]
            self.constraints.append("primary key ({0})".format(",".join(f.name for f in self.pk)))
        else:
            for f in fields:
                if f.pk:
                    self.pk = f
                    break
        for f in fields:
            f.table = self
        self.tables[name] = self

    def get_field(self, name):
        for f in self.fields:
            if f.name == name:
                return f
        return None

    def __str__(self):
        base = "create table {0} (\n".format(self.name)
        fields = [str(f) for f in self.fields]
        constraints = ["constraint " + f.constraint for f in self.fields if f.constraint is not None]
        base += ",\n".join(" " * 4 + s for s in fields + constraints + self.constraints)
        base += "\n);"
        return base


class Field(object):
    def __init__(self, name, type, not_null=True, pk=False, fk=None, unique=False):
        self.name = name
        self.type = type
        self.not_null = not_null and not pk
        self.unique = unique
        self.pk = pk
        self.fk = fk and Table.tables[fk[0]].get_field(fk[1])
        self.constraint = None

    def __str__(self):
        base = "{0} {1}".format(self.name, self.type)
        if self.pk:
            base += " primary key"
        if self.fk:
            base += " references {0} ({1}) on delete cascade on update cascade".format(
                self.fk.table.name, self.fk.name)
        if self.not_null:
            base += " not null"
        if self.unique :
            base += " unique"
        return base


class FieldInteger(Field):
    def __init__(self, name, *args, **kwargs):
        super(FieldInteger, self).__init__(name, "integer", *args, **kwargs)

class FieldText(Field):
    def __init__(self, name, *args, **kwargs):
        super(FieldText, self).__init__(name, "text", *args, **kwargs)

class FieldDate(FieldInteger):
    def __init__(self, *args, **kwargs):
        super(FieldDate, self).__init__(*args, **kwargs)
        self.constraint = "date_{0} check ({0} > 0)".format(self.name)

class FieldBool(FieldInteger):
    def __init__(self, *args, **kwargs):
        super(FieldBool, self).__init__(*args, **kwargs)
        self.constraint = "bool_{0} check ({0} in (0,1))".format(self.name)

class FieldEnum(FieldText):
    def __init__(self, name, values, *args, **kwargs):
        super(FieldEnum, self).__init__(name, *args, **kwargs)
        self.values = values
        self.constraint = "enum_{0} check ({0} in ({1}))".format(self.name, ",".join('"{0}"'.format(v) for v in values))

tables = [
    Table("companies",
        FieldInteger("id", pk=True),
        FieldText("name", unique=True)),
    Table("projects",
        FieldInteger("id", pk=True),
        FieldDate("begin_date"),
        FieldDate("end_date")),
    Table("developers",
        FieldText("full_name"),
        FieldText("username", pk=True),
        FieldInteger("company_id", fk=("companies", "id")),
        FieldText("password"),
        FieldBool("is_admin")),
    Table("developers_distribution",
        FieldText("developer_username", fk=("developers", "username")),
        FieldInteger("project_id", fk=("projects", "id")),
        FieldBool("is_manager"),
        pk=("developer_username", "project_id")),
    Table("tasks",
        FieldInteger("id", pk=True),
        FieldText("title"),
        FieldText("description"),
        FieldInteger("project_id", fk=("projects", "id")),
        FieldInteger("hours"),
        FieldEnum("status", ("active", "finished", "delayed"))),
    Table("tasks_dependencies",
        FieldInteger("task_id", fk=("tasks", "id")),
        FieldInteger("depended_task_id", fk=("tasks", "id")),
        pk=("task_id", "depended_task_id")),
    Table("contracts",
        FieldInteger("number", pk=True),
        FieldInteger("company_id", fk=("companies", "id")),
        FieldInteger("project_id", fk=("projects", "id")),
        FieldDate("date_of_creation"),
        FieldEnum("status", ("active", "finished", "delayed"))),
    Table("reports",
        FieldInteger("id", pk=True),
        FieldText("developer_username", fk=("developers", "username")),
        FieldInteger("task_id", fk=("tasks", "id")),
        FieldDate("begin_date"),
        FieldDate("end_date"),
        FieldText("description"))
]
