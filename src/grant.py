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

from designer.mainwindow import Ui_MainWindow
from designer.about_dialog import Ui_AboutDialog
from designer.login_dialog import Ui_LoginDialog
from designer.add_admin_dialog import Ui_AddAdminDialog
from designer.select_database_dialog import Ui_SelectDatabase

import gui.records
import gui.viewtables

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

class AboutDialog(QtGui.QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.ui = Ui_AboutDialog()
        self.ui.setupUi(self)


class LoginDialog(QtGui.QDialog):
    login = QtCore.pyqtSignal(str, str)
    def __init__(self, parent):
        super().__init__(parent)

        self.ui = Ui_LoginDialog()
        self.ui.setupUi(self)

        self.accepted.connect(self.emitAccepted)

    @QtCore.pyqtSlot()
    def emitAccepted(self):
        self.login.emit(self.ui.usernameEdit.text(),
            self.ui.passwordEdit.text())

    def showEvent(self, event):
        self.ui.usernameEdit.clear()
        self.ui.passwordEdit.clear()


class SelectDatabaseDialog(QtGui.QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.ui = Ui_SelectDatabase()
        self.ui.setupUi(self)
        self.ui.lineEdit.setText(
            os.path.join(CURRENT_PATH, 'new_database.db'))

        self.ui.pushButton.clicked.connect(self.showDialog)
        self.accepted.connect(
            lambda: app.adjust_database(self.ui.lineEdit.text()))

    @QtCore.pyqtSlot()
    def showDialog(self):
        filename = QtGui.QFileDialog.getOpenFileName(self,
            'Open database file', CURRENT_PATH)
        if len(filename):
            self.ui.lineEdit.setText(filename)


class AddAdminDialog(QtGui.QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.ui = Ui_AddAdminDialog()
        self.ui.setupUi(self)
        self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).setDisabled(True)
        self.edits = self.ui.fullNameEdit, self.ui.usernameEdit,\
            self.ui.passwordEdit, self.ui.companyNameEdit

        for edit in self.edits:
            edit.textChanged.connect(self.emptiness_validator)
        self.accepted.connect(lambda: app.add_new_admin(
            self.ui.usernameEdit.text(),
            self.ui.passwordEdit.text(),
            self.ui.fullNameEdit.text(),
            self.ui.companyNameEdit.text()))

    def emptiness_validator(self, text):
        self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).setDisabled(not all(len(edit.text()) for edit in self.edits))


class MainWindow(QtGui.QMainWindow):
    def tableTrigger(self, tablename):
        return lambda: self.createTableView(tablename)

    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.center()

        self.about_dialog = AboutDialog(self)
        self.login_dialog = LoginDialog(self)
        self.select_database = SelectDatabaseDialog(self)

        self.ui.actionAbout.triggered.connect(self.about_dialog.open)
        self.ui.actionLogin.triggered.connect(self.login_dialog.open)
        self.ui.actionCompanies.triggered.connect(self.tableTrigger('companies'))
        self.ui.actionDevelopers.triggered.connect(self.tableTrigger('developers'))
        self.ui.actionProjects.triggered.connect(self.tableTrigger('projects'))
        self.ui.actionContracts.triggered.connect(self.tableTrigger('contracts'))
        self.ui.actionTasks.triggered.connect(self.tableTrigger('tasks'))
        self.ui.actionReports.triggered.connect(self.tableTrigger('reports'))
        self.ui.actionDevelopers_Distribution.triggered.connect(self.tableTrigger('developers_distribution'))
        self.ui.actionTasks_Dependencies.triggered.connect(self.tableTrigger('tasks_dependencies'))
        self.select_database.rejected.connect(self.close)
        self.login_dialog.login.connect(app.login)

        self.statusBarText = QtGui.QLabel()
        self.statusBar().addPermanentWidget(self.statusBarText)
        self.showStatusMessage('Not logged in')

        self.select_database.open()
        self.set_actions()

    def createTableView(self, tablename):
        cls = gui.viewtables.ViewTableForm
        clsmaps = {'companies': gui.viewtables.CompaniesViewTableForm,
            'developers_distribution': gui.viewtables.DevelopersDistributionTableForm,
            'tasks': gui.viewtables.TasksTableForm }
        if tablename in clsmaps:
            cls = clsmaps[tablename]
        table_widget = cls(self, tablename)
        self.ui.mdiArea.addSubWindow(table_widget)
        table_widget.show()

    def center(self):
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)

    def addAdminDialogOpen(self):
        self.add_admin_dialog = AddAdminDialog(self)
        self.add_admin_dialog.rejected.connect(self.close)
        self.add_admin_dialog.open()

    def set_actions(self, disabled=True):
        ui = self.ui
        actions = [
            ui.actionCompanies,
            ui.actionDevelopers
        ]
        for action in actions:
            action.setDisabled(disabled)

    def showStatusMessage(self, text):
        self.statusBarText.setText(text)


class GrantApplication(QtGui.QApplication):
    noadmins = QtCore.pyqtSignal()

    def exec_(self):
        self.mainwindow = MainWindow()
        self.mainwindow.showNormal()
        super().exec_()

    def adjust_database(self, filename):
        self.grant = Grant(echo=True, dbname=filename)
        self.noadmins.connect(self.mainwindow.addAdminDialogOpen)
        if not self.grant.has_admins():
            self.noadmins.emit()
        else:
            self.session = self.login('admin', 'admin')

    def add_new_admin(self, username, password, fullname, company):
        self.grant.add_first_admin(username, password, fullname, company)
        self.session = self.login(username, password)

    @QtCore.pyqtSlot(str, str)
    def login(self, username, password):
        is_admin = self.grant.get_user(username, password)
        if is_admin is not None:
            for w in app.mainwindow.ui.mdiArea.subWindowList():
                    w.close()
            self.session = Session(self, username=username, password=password, is_admin=is_admin)
            self.mainwindow.set_actions(False)
            self.mainwindow.showStatusMessage('Logged in as {0} {1}'.format(username, "[admin]" if is_admin else ""))
            return self.session
        else:
            mbox = QtGui.QMessageBox(
                QtGui.QMessageBox.Critical,
                'Error',
                'User or password is incorrect',
                QtGui.QMessageBox.Ok)
            mbox.exec()
            return None

app = GrantApplication(sys.argv)
gui.records.app = gui.viewtables.app = app
sys.exit(app.exec_())
