from PyQt4 import QtGui, QtCore
from designer.view_table_widget import Ui_ViewTableForm

from gui.records import *

class ViewTableForm(QtGui.QWidget):
    def __init__(self, parent, tablename):
        super().__init__(parent)

        self.ui = Ui_ViewTableForm()
        self.ui.setupUi(self)

        ui = self.ui
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
        if app.session.is_admin:
            ui.tableWidget.cellDoubleClicked.connect(self.editRecord)
            ui.tableWidget.itemSelectionChanged.connect(self.adjust_actions)
        else:
            ui.addRecord.setDisabled(True)
        self.tablename = tablename
        self.RecordClass = globals()[tablename.capitalize() + "RecordForm"]

        self.setWindowTitle("View {0}".format(tablename))

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
        self.headers = [h for h in app.session.get_fields_description(self.tablename) if not h.hidden]

        cols = len(self.headers)
        self.ui.tableWidget.setColumnCount(cols)
        self.ui.tableWidget.setHorizontalHeaderLabels([h.verbose_name for h in self.headers])
        self.updateTable()

    def postUpdateActions(self):
        pass

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
                item = QtGui.QTableWidgetItem(self.headers[j].convert(v))
                item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
                self.ui.tableWidget.setItem(i, j, item)

        self.postUpdateActions()

    @QtCore.pyqtSlot(int, int)
    def editRecord(self, row, col):
        rec = self.RecordClass(self, self.tablename, self.pkeys[row])
        rec.open()

    def addRecord(self):
        rec = self.RecordClass(self, self.tablename)
        rec.open()

    def error(self, text):
        mbox = QtGui.QMessageBox(
            QtGui.QMessageBox.Critical,
            'Error',
            text,
            QtGui.QMessageBox.Ok)
        mbox.exec()


class CompaniesViewTableForm(ViewTableForm):
    @QtCore.pyqtSlot()
    def deleteActionTriggered(self):
        row = self.ui.tableWidget.currentRow()
        if self.pkeys[row][0] == 1:
            self.error("Cann't delete your company")
        else:
            super(CompaniesViewTableForm, self).deleteActionTriggered()

class DevelopersDistributionTableForm(ViewTableForm):
    def postUpdateActions(self):
        self.bypass = app.session.is_admin
        if not self.bypass:
            self.managed_prjs = app.session.get_managed_projects()
            if len(self.managed_prjs):
                self.managed_prjs = set(p for p, in self.managed_prjs)
                self.ui.addRecord.setDisabled(False)
                self.ui.tableWidget.cellDoubleClicked.connect(self.editRecord)
                self.ui.tableWidget.itemSelectionChanged.connect(self.adjust_actions)

    @QtCore.pyqtSlot(int, int)
    def editRecord(self, row, col):
        if self.bypass or self.pkeys[row][1] in self.managed_prjs:
            super().editRecord(row, col)

    @QtCore.pyqtSlot()
    def adjust_actions(self):
        row = self.ui.tableWidget.currentRow()
        val = len(self.ui.tableWidget.selectedItems()) == 0
        val = val and (self.bypass or self.pkeys[row][1] in self.managed_prjs)
        self.ui.editRecord.setDisabled(val)
        self.ui.deleteRecord.setDisabled(val)

class TasksTableForm(ViewTableForm):
    def postUpdateActions(self):
        self.bypass = app.session.is_admin
        self.projects_id = None
        if not self.bypass:
            self.managed_prjs = app.session.get_managed_projects()
            if len(self.managed_prjs):
                self.projects_id = [p for p, in app.session.get_tasks_projects_id()]
                self.managed_prjs = set(p for p, in self.managed_prjs)
                self.ui.addRecord.setDisabled(False)
                self.ui.tableWidget.cellDoubleClicked.connect(self.editRecord)
                self.ui.tableWidget.itemSelectionChanged.connect(self.adjust_actions)

    @QtCore.pyqtSlot(int, int)
    def editRecord(self, row, col):
        if self.bypass or (self.projects_id and self.projects_id[row] in self.managed_prjs):
            super().editRecord(row, col)

    @QtCore.pyqtSlot()
    def adjust_actions(self):
        row = self.ui.tableWidget.currentRow()
        val = len(self.ui.tableWidget.selectedItems()) == 0
        val = val and (self.bypass or (self.projects_id and self.projects_id[row] in self.managed_prjs))
        self.ui.editRecord.setDisabled(val)
        self.ui.deleteRecord.setDisabled(val)

class TasksDependenciesForm(ViewTableForm):
    def postUpdateActions(self):
        self.bypass = app.session.is_admin
        self.projects_id = None
        if not self.bypass:
            self.managed_prjs = app.session.get_managed_projects()
            if len(self.managed_prjs):
                self.projects_id = [p for p, in app.session.get_tasks_dependencies_projects_id()]
                self.managed_prjs = set(p for p, in self.managed_prjs)
                self.ui.addRecord.setDisabled(False)
                self.ui.tableWidget.cellDoubleClicked.connect(self.editRecord)
                self.ui.tableWidget.itemSelectionChanged.connect(self.adjust_actions)

    @QtCore.pyqtSlot(int, int)
    def editRecord(self, row, col):
        if self.bypass or (self.projects_id and self.projects_id[row] in self.managed_prjs):
            super().editRecord(row, col)

    @QtCore.pyqtSlot()
    def adjust_actions(self):
        row = self.ui.tableWidget.currentRow()
        val = len(self.ui.tableWidget.selectedItems()) == 0
        val = val and (self.bypass or (len(self.projects_id) != 0 and self.projects_id[row] in self.managed_prjs))
        self.ui.editRecord.setDisabled(val)
        self.ui.deleteRecord.setDisabled(val)

class ReportsForm(ViewTableForm):
    def postUpdateActions(self):
        self.bypass = app.session.is_admin

    @QtCore.pyqtSlot(int, int)
    def editRecord(self, row, col):
        if self.bypass or self.ui.tableWidget.item(row, 0).text() == app.session.username:
            super().editRecord(row, col)

    @QtCore.pyqtSlot()
    def adjust_actions(self):
        row = self.ui.tableWidget.currentRow()
        item = self.ui.tableWidget.item(row, 0)
        username = item.text()
        val = len(self.ui.tableWidget.selectedItems()) == 0
        val = self.bypass or (val and username == app.session.username)
        self.ui.editRecord.setDisabled(val)
        self.ui.deleteRecord.setDisabled(val)
