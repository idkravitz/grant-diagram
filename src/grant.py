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
from grant_core.init_tables import Table, FieldInteger, FieldText, FieldBool, FieldDate, FieldEnum

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
    login = QtCore.pyqtSignal(str, str)
    def __init__(self, parent):
        super(LoginDialog, self).__init__(parent)

        self.ui = Ui_LoginDialog()
        self.ui.setupUi(self)

        self.accepted.connect(self.emitAccepted)

    @QtCore.pyqtSlot()
    def emitAccepted(self):
        self.login.emit(self.ui.usernameEdit.text(), self.ui.passwordEdit.text())

    def showEvent(self, event):
        self.ui.usernameEdit.clear()
        self.ui.passwordEdit.clear()


class SelectDatabaseDialog(QtGui.QDialog):
    def __init__(self, parent):
        global app
        super(SelectDatabaseDialog, self).__init__(parent)

        self.ui = Ui_SelectDatabase()
        self.ui.setupUi(self)
        self.ui.lineEdit.setText(os.path.join(CURRENT_PATH, 'new_database.db'))

        self.ui.pushButton.clicked.connect(self.showDialog)
        self.accepted.connect(lambda: app.adjust_database(self.ui.lineEdit.text()))

    @QtCore.pyqtSlot()
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
            edit.textChanged.connect(self.emptiness_validator)
        self.accepted.connect(lambda: app.add_new_admin(
            self.ui.usernameEdit.text(),
            self.ui.passwordEdit.text(),
            self.ui.fullNameEdit.text(),
            self.ui.companyNameEdit.text()))

    def emptiness_validator(self, text):
        self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).setDisabled(not all(len(edit.text()) for edit in self.edits))

class RecordForm(QtGui.QDialog):
    def __init__(self, parent, tablename, pkey=None):
        super(RecordForm, self).__init__(parent)
        self.setModal(True)
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.gbox = QtGui.QGridLayout(self)

        fields = app.session.get_fields_description(tablename)
        self.pkey = pkey
        self.tablename = tablename
        rec = pkey and app.session.get_record(tablename, pkey)
        row = 0
        self.ctrls = []
        for i, f in enumerate(fields):
            if not (f.hidden and f.pk):
                self.place_control(row, f, rec and rec[i])
                row += 1
        self.gbox.addWidget(self.buttonBox, row, 1, 1, 1)
        self.setLayout(self.gbox)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        if pkey is not None:
            self.accepted.connect(self.updateRecord)
        else:
            self.accepted.connect(self.addRecord)

    def _get_values(self):
        values = []
        for ctrl in self.ctrls:
            if type(ctrl) is QtGui.QLineEdit:
                value = ctrl.text()
            elif type(ctrl) is QtGui.QCheckBox:
                value = ctrl.isChecked()
            elif type(ctrl) is QtGui.QComboBox:
                value = ctrl.itemData(ctrl.currentIndex())
            values.append(value)
        return values

    def updateRecord(self):
        values = self._get_values()
        app.session.update_record(self.tablename, values, list(self.pkey))
        for w in app.mainwindow.ui.mdiArea.subWindowList():
            w.widget().updateTable()

    def addRecord(self):
        values = self._get_values()
        app.session.add_record(self.tablename, values)
        for w in app.mainwindow.ui.mdiArea.subWindowList():
            w.widget().updateTable()

    def place_control(self, row, field, value=None):
        label = QtGui.QLabel(self)
        label.setText(field.name)
        self.gbox.addWidget(label, row, 0, 1, 1)
        if field.fk:
            ctrl = QtGui.QComboBox(self)
            items = app.session.get_fk_values(field)
            for n, i in enumerate(items):
                ctrl.addItem(i[1], i[0])
                if value is not None and value == i[0]:
                    ctrl.setCurrentIndex(n)
        elif type(field) is FieldBool:
            ctrl = QtGui.QCheckBox(self)
            if value is not None:
                ctrl.setChecked(value == 1)
        elif type(field) is FieldDate:
            pass
        elif type(field) is FieldEnum:
            pass
        else:
            ctrl = QtGui.QLineEdit(self)
            if value is not None:
                ctrl.setText(field.convert(value))
        self.ctrls.append(ctrl)
        self.gbox.addWidget(ctrl, row, 1, 1, 1)



class ViewTableForm(QtGui.QWidget):
    def __init__(self, parent, tablename):
        super(ViewTableForm, self).__init__(parent)

        self.ui = Ui_ViewTableForm()
        self.ui.setupUi(self)

        ui = self.ui
        if app.session.is_admin:
            ui.toolbar = QtGui.QToolBar('Tools', self)
            ui.verticalLayout.insertWidget(0, self.ui.toolbar)
            ui.addRecord = QtGui.QAction('Add', self)
            ui.addRecord.triggered.connect(self.addRecord)
            ui.editRecord = QtGui.QAction('Edit', self)
            ui.editRecord.setDisabled(True)
            ui.editRecord.triggered.connect(self.editActionTriggered)
            ui.deleteRecord = QtGui.QAction('Delete', self)
            ui.deleteRecord.setDisabled(True)
            ui.deleteRecord.triggered.connect(self.deleteActionTriggered)
            for action in [ui.addRecord, ui.editRecord, ui.deleteRecord]:
                ui.toolbar.addAction(action)
            ui.tableWidget.cellDoubleClicked.connect(self.editRecord)
            ui.tableWidget.itemSelectionChanged.connect(self.adjust_actions)
        self.tablename = tablename

        self.setWindowTitle(tablename)

        self._fillTable()


    @QtCore.pyqtSlot()
    def adjust_actions(self):
        val = len(self.ui.tableWidget.selectedItems()) == 0
        self.ui.editRecord.setDisabled(val)
        self.ui.deleteRecord.setDisabled(val)

    @QtCore.pyqtSlot()
    def editActionTriggered(self):
        row = self.ui.tableWidget.currentRow()
        self.editRecord(row, 0)

    @QtCore.pyqtSlot()
    def deleteActionTriggered(self):
        reply = QtGui.QMessageBox.question(self, 'Message',
            'Are you sure to delete this record ?',
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            row = self.ui.tableWidget.currentRow()
            app.session.delete_record(self.tablename, self.pkeys[row])
            for w in app.mainwindow.ui.mdiArea.subWindowList():
                w.widget().updateTable()


    def _fillTable(self):
        self.headers = app.session.get_headers(self.tablename)

        cols = len(self.headers)
        self.ui.tableWidget.setColumnCount(cols)
        self.ui.tableWidget.setHorizontalHeaderLabels([h[0] for h in self.headers])
        self.updateTable()


    def updateTable(self):
        self.ui.tableWidget.clearContents()

        values = app.session.get_table(self.tablename)
        rows = len(values)
        self.ui.tableWidget.setRowCount(rows)
        if rows:
            self.pkeys = []
            pklen = len(values[0]) - self.ui.tableWidget.columnCount()
        for i, r in enumerate(values):
            self.pkeys.append(r[:pklen])
            for j, v in enumerate(r[pklen:]):
                item = QtGui.QTableWidgetItem(self.headers[j][1].convert(v))
                item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
                self.ui.tableWidget.setItem(i, j, item)

    @QtCore.pyqtSlot(int, int)
    def editRecord(self, row, col):
        rec = RecordForm(self, self.tablename, self.pkeys[row])
        rec.open()

    def addRecord(self):
        rec = RecordForm(self, self.tablename)
        rec.open()

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        global app
        super(MainWindow, self).__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.center()

        self.about_dialog = AboutDialog(self)
        self.login_dialog = LoginDialog(self)
        self.select_database = SelectDatabaseDialog(self)

        self.ui.actionAbout.triggered.connect(self.about_dialog.open)
        self.ui.actionLogin.triggered.connect(self.login_dialog.open)
        self.ui.actionCompanies.triggered.connect(lambda: self.createTableView('companies'))
        self.ui.actionDevelopers.triggered.connect(lambda: self.createTableView('developers'))
        self.select_database.rejected.connect(self.close)
        self.login_dialog.login.connect(app.login)

        self.statusBarText = QtGui.QLabel()
        self.statusBar().addPermanentWidget(self.statusBarText)
        self.showStatusMessage('Not logged in')

        self.select_database.open()
        self.set_actions()

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
        super(GrantApplication, self).exec_()

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
            self.session = Session(self, username=username, password=password, is_admin=is_admin)
            self.mainwindow.set_actions(False)
            self.mainwindow.showStatusMessage('Logged as {0}{1}'.format(username, "[admin]" if is_admin else ""))
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
sys.exit(app.exec_())
