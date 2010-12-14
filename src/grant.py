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

from designer.mainwindow import Ui_MainWindow
from designer.about_dialog import Ui_AboutDialog
from designer.login_dialog import Ui_LoginDialog
from designer.select_database_dialog import Ui_SelectDatabase

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
        super(SelectDatabaseDialog, self).__init__(parent)

        self.ui = Ui_SelectDatabase()
        self.ui.setupUi(self)
        self.ui.lineEdit.setText(os.path.join(CURRENT_PATH, 'new_database.db'))

        self.connect(self.ui.pushButton, QtCore.SIGNAL('clicked()'), self.showDialog)

    def showDialog(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open database file', CURRENT_PATH)
        if len(filename):
            self.ui.lineEdit.setText(filename)


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
        self.connect(self.select_database, QtCore.SIGNAL('rejected()'), self, QtCore.SLOT('close()'))

    def showEvent(self, event):
        self.select_database.open()

    def center(self):
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)

class GrantApplication(QtGui.QApplication):
    def __init__(self, argv):
        super(GrantApplication, self).__init__(argv)

app = GrantApplication(sys.argv)
mainwindow = MainWindow()
mainwindow.show()
sys.exit(app.exec_())
