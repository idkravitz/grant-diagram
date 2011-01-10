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
        ui.tableWidget.cellDoubleClicked.connect(self.editRecord)
        ui.tableWidget.itemSelectionChanged.connect(self.adjust_actions)
        if not app.session.is_admin:
            ui.addRecord.setDisabled(True)
        self.tablename = tablename
        self.RecordClass = globals()[tablename.capitalize() + "RecordForm"]

        self.setWindowTitle("View {0}".format(tablename))

        self._fillTable()

    @QtCore.pyqtSlot()
    def adjust_actions(self):
        val = not app.session.is_admin or len(self.ui.tableWidget.selectedItems()) == 0
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

        self.adjustColumnsWidth()
        self.postUpdateActions()

    def adjustColumnsWidth(self):
        tw = self.ui.tableWidget
        tw.resizeColumnsToContents()

    @QtCore.pyqtSlot(int, int)
    def editRecord(self, row, col):
        if app.session.is_admin:
            self._spawnEditDialog(row)

    def _spawnEditDialog(self, row, *args, **kwargs):
        rec = self.RecordClass(self, self.tablename, self.pkeys[row], *args, **kwargs)
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
            super().deleteActionTriggered()

class ContractsViewTableForm(ViewTableForm):
    @QtCore.pyqtSlot(int, int)
    def editRecord(self, row, col):
        if not app.grant.has_projects():
            self.error('You have no projects')
        else:
            super().editRecord(row, col)

    def addRecord(self):
        if not app.grant.has_projects():
            self.error('You have no projects')
        else:
            super().addRecord()


class DevelopersDistributionTableForm(ViewTableForm):
    def postUpdateActions(self):
        self.bypass = app.session.is_admin
        if not self.bypass:
            self.managed_prjs = app.session.get_managed_projects()
            if len(self.managed_prjs):
                self.managed_prjs = set(p for p, in self.managed_prjs)
                self.ui.addRecord.setDisabled(False)

    @QtCore.pyqtSlot(int, int)
    def editRecord(self, row, col):
        if not app.grant.has_projects():
            self.error('You have no projects')
        elif not app.grant.has_developers():
            self.error('You have no developers')
        elif self.bypass or self.pkeys[row][1] in self.managed_prjs:
            self._spawnEditDialog(row)

    def addRecord(self):
        if not app.grant.has_projects():
            self.error('You have no projects')
        elif not app.grant.has_developers():
            self.error('You have no developers')
        else:
            super().addRecord()

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
            self.projects_id = [p for p, in app.session.get_tasks_projects_id()]
            self.managed_prjs = app.session.get_managed_projects() or ()
            self.distributed_to = app.session.get_distributed_to() or ()
            self.distributed_to = set(p for p, in self.distributed_to)
            if len(self.managed_prjs):
                self.managed_prjs = set(p for p, in self.managed_prjs)
                self.ui.addRecord.setDisabled(False)

    @QtCore.pyqtSlot(int, int)
    def editRecord(self, row, col):
        if not app.grant.has_projects():
            self.error('You have no projects')
        elif self.bypass or (self.projects_id and (self.projects_id[row] in self.managed_prjs or
            (self.projects_id[row] in self.distributed_to and
                self.ui.tableWidget.item(row, self.ui.tableWidget.columnCount() - 1).text() == 'active'))):
            self._spawnEditDialog(row, is_not_manager= not (self.bypass or (self.projects_id and (self.projects_id[row] in self.managed_prjs))))

    def addRecord(self):
        if not app.grant.has_projects():
            self.error('You have no projects')
        else:
            super().addRecord()

    @QtCore.pyqtSlot()
    def adjust_actions(self):
        row = self.ui.tableWidget.currentRow()
        val = len(self.ui.tableWidget.selectedItems()) == 0
        val1 = not val and (self.bypass or (self.projects_id and self.projects_id[row] in self.managed_prjs))
        val2 = not val and (self.bypass or (self.projects_id and self.projects_id[row] in self.distributed_to and
            self.ui.tableWidget.item(row, self.ui.tableWidget.columnCount() - 1).text() == 'active'))
        self.ui.editRecord.setDisabled(not (val2 or val1))
        self.ui.deleteRecord.setDisabled(not val1)

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

    @QtCore.pyqtSlot(int, int)
    def editRecord(self, row, col):
        if not app.grant.has_tasks():
            self.error('You have no tasks')
        elif self.bypass or (self.projects_id and self.projects_id[row] in self.managed_prjs):
            self._spawnEditDialog(row)

    def addRecord(self):
        if not app.grant.has_tasks():
            self.error('You have no tasks')
        else:
            super().addRecord()

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
        if app.session.has_distributed():
            self.ui.addRecord.setDisabled(False)

    @QtCore.pyqtSlot(int, int)
    def editRecord(self, row, col):
        if not app.grant.has_tasks():
            self.error('You have no tasks')
        elif not app.grant.has_distributed_developers():
            self.error('You have no distributed developers')
        elif self.bypass or self.ui.tableWidget.item(row, 0).text() == app.session.username:
            self._spawnEditDialog(row)

    @QtCore.pyqtSlot()
    def adjust_actions(self):
        row = self.ui.tableWidget.currentRow()
        item = self.ui.tableWidget.item(row, 0)
        username = item.text()
        enable = len(self.ui.tableWidget.selectedItems()) != 0
        enable = self.bypass or (enable and username == app.session.username)
        self.ui.editRecord.setDisabled(not enable)
        self.ui.deleteRecord.setDisabled(not enable)
