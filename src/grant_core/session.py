STRING = "string"
INT = "int"
BOOL = "bool"

class Session(object):
    COMMON = set({'logout'})
    ADMIN_ONLY = set({'add_developer','add_company'})
    AUTHORIZED_ONLY = set({'logout'})
    def __init__(self, aplication, username=None, password=None, is_admin=False):
        self.aplication = aplication
        self.grant = self.aplication.grant
        self.is_admin = is_admin
        self.username = username
        self.password = password

    def correct_args(self, args, types):
        def correct_type(type_rec, arg):
            if type_rec is tuple:
                return arg.type in type_reс
            return arg.type == type_rec

        return all(correct_type(t, a) for t, a in zip(types, args))

    def process_commands(self, command, args):
        print(args)
        if self.username is None and command in self.AUTHORIZED_ONLY:
            return "Can't use {0} in unauthorized mode".format(command)
        if (self.is_admin and command in self.ADMIN_ONLY) or (command in self.COMMON):
            return getattr(self, command)(*args)
        return "Unknown command {0}".format(command)

    def logout(self):
        self.aplication.session = None

    def add_developer(self, username, password, fullname, company, is_admin):
        self.grant.add_developer(username, password, fullname, company, is_admin)
        return "developer added"

    def add_company(self, name):
        self.grant.add_company(name)
        return "company added"
