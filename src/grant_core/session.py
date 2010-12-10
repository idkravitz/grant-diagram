class Session(object):
    COMMON = set({'logout','login','get_companies'})
    ADMIN_ONLY = set({'add_developer','add_company'})
    AUTHORIZED_ONLY = set({})
    def __init__(self, application, username=None, password=None, is_admin=False):
        self.application = application
        self.grant = self.application.grant
        self.is_admin = is_admin
        self.username = username
        self.password = password

    def process_commands(self, command, args):
        if self.username is None and command in self.AUTHORIZED_ONLY:
            return "Can't use {0} in unauthorized mode".format(command)
        if (self.is_admin and command in self.ADMIN_ONLY) or (command in self.COMMON):
            return getattr(self, command)(*args)
        return "Unknown command {0}".format(command)

    def logout(self):
        self.application.session = None
        return "Successfully logged out"

    def login(self, username, password):
        print(self.logout())
        return self.application.login(username, password)

    def add_developer(self, username, password, fullname, company, is_admin):
        self.grant.add_developer(username, password, fullname, company, is_admin)
        return "developer added"

    def add_company(self, name):
        self.grant.add_company(name)
        return "company added"

    def get_companies(self):
        return self.grant.get_companies()

    def __repr__(self):
        return '<Session (username => "{0}")>'.format(self.username)
