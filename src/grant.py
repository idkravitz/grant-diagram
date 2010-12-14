#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Grant diagram project management tool
task is located at http://iexperts.ru/files/task2010.rar

This is an entry point for GUI interface on PyQt
"""

import os
import sys

from PyQt4 import QtGui, QtCore

from grant_core.libdb import Grant
from grant_core.session import Session
from grant_core.init_tables import Table

from designer.mainwindow import Ui_MainWindow
from designer.about_dialog import Ui_AboutDialog
from designer.login_dialog import Ui_LoginDialog
from designer.add_admin_dialog import Ui_AddAdminDialog
from designer.select_database_dialog import Ui_SelectDatabase
from designer.view_table_widget import Ui_ViewTableForm

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

class AboutDialog(QtGui.QDialog):
    def __init__(self, parent):
        super(AboutDialog, self).__init__(parent)

        self.ui = Ui_AboutDialog()
        self.ui.setupUi(self)

class LoginDialog(QtGui.QDialog):
    def __init__(self, parent):
        super(LoginDialog, self).__init__(parent)

        self.ui = Ui_LoginDialog()
        self.ui.setupUi(self)

class SelectDatabaseDialog(QtGui.QDialog):
    def __init__(self, parent):
        global app
        super(SelectDatabaseDialog, self).__init__(parent)

        self.ui = Ui_SelectDatabase()
        self.ui.setupUi(self)
        self.ui.lineEdit.setText(os.path.join(CURRENT_PATH, 'new_database.db'))

        self.connect(self.ui.pushButton, QtCore.SIGNAL('clicked()'), self.showDialog)
        self.connect(self, QtCore.SIGNAL('accepted()'), lambda: app.adjust_database(self.ui.lineEdit.text()))

    def showDialog(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open database file', CURRENT_PATH)
        if len(filename):
            self.ui.lineEdit.setText(filename)

class AddAdminDialog(QtGui.QDialog):
    def __init__(self, parent):
        super(AddAdminDialog, self).__init__(parent)

        self.ui = Ui_AddAdminDialog()
        self.ui.setupUi(self)
        self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).setDisabled(True)
        self.edits = self.ui.fullNameEdit, self.ui.usernameEdit, self.ui.passwordEdit, self.ui.companyNameEdit

        for edit in self.edits:
            self.connect(edit, QtCore.SIGNAL('textChanged(const QString&)'), self.emptiness_validator)
        self.connect(self, QtCore.SIGNAL('accepted()'),
            lambda: app.add_new_admin(self.ui.usernameEdit.text(), self.ui.passwordEdit.text(),
                self.ui.fullNameEdit.text(), self.ui.companyNameEdit.text()))

    def emptiness_validator(self, text):
        self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).setDisabled(not all(len(edit.text()) for edit in self.edits))

class ViewTableForm(QtGui.QWidget):
    def __init__(self, parent, tablename):
        super(ViewTableForm, self).__init__(parent)

        self.ui = Ui_ViewTableForm()
        self.ui.setupUi(self)

        values = app.grant.get_table(tablename)

        rows = len(values)
        if rows:
            cols = len(values[0])
            self.ui.tableWidget.setRowCount(rows)
            self.ui.tableWidget.setColumnCount(cols)
        for i, r in enumerate(values):
            for j, v in enumerate(r):
                item = QtGui.QTableWidgetItem(str(v))
                item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
                self.ui.tableWidget.setItem(i, j, item)

        self.ui.tableWidget.setHorizontalHeaderLabels([f.name for f in Table.tables[tablename].fields])


class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.center()
        self.about_dialog = AboutDialog(self)
        self.login_dialog = LoginDialog(self)
        self.select_database = SelectDatabaseDialog(self)

        self.connect(self.ui.actionAbout, QtCore.SIGNAL('triggered()'), self.about_dialog, QtCore.SLOT('open()'))
        self.connect(self.ui.actionLogin, QtCore.SIGNAL('triggered()'), self.login_dialog, QtCore.SLOT('open()'))
        self.connect(self.ui.actionCompanies, QtCore.SIGNAL('triggered()'), lambda: self.createTableView('companies'))
        self.connect(self.ui.actionDevelopers, QtCore.SIGNAL('triggered()'), lambda: self.createTableView('developers'))
        self.connect(self.select_database, QtCore.SIGNAL('rejected()'), self, QtCore.SLOT('close()'))

        self.select_database.open()

    def createTableView(self, tablename):
        table_widget = ViewTableForm(self, tablename)
        self.ui.mdiArea.addSubWindow(table_widget)
        table_widget.show()

    def center(self):
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)

    def addAdminDialogOpen(self):
        self.add_admin_dialog = AddAdminDialog(self)
        self.add_admin_dialog.open()
        self.connect(self.add_admin_dialog, QtCore.SIGNAL('rejected()'), self, QtCore.SLOT('close()'))


class GrantApplication(QtGui.QApplication):
    def __init__(self, argv):
        super(GrantApplication, self).__init__(argv)
        self.mainwindow = MainWindow()
        self.mainwindow.showNormal()

    def adjust_database(self, filename):
        self.grant = Grant(echo=False, dbname=filename)
        self.connect(self, QtCore.SIGNAL('noadmins'), self.mainwindow.addAdminDialogOpen)
        if not self.grant.has_admins():
            self.emit(QtCore.SIGNAL('noadmins'))

    def add_new_admin(self, username, password, fullname, company):
        self.grant.add_first_admin(username, password, fullname, company)
        self.session = self.login(username, password)
        print(self.session)

    def login(self, username, password):
        is_admin = self.grant.get_user(username, password)
        if is_admin is not None:
            self.session = Session(self, username=username, password=password, is_admin=is_admin)
            return self.session
        else:
            return 'Unknown user or wrong password' # raise exception instead

app = GrantApplication(sys.argv)
sys.exit(app.exec_())
