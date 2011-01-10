from PyQt4 import QtGui, QtCore
from designer.activities_form import Ui_activitiesForm
from grant_core.init_tables import Table

class ActivitiesForm(QtGui.QWidget):
    readyForReport = QtCore.pyqtSignal((), (int,))

    def __init__(self, parent):
        super().__init__(parent)

        self.ui = Ui_activitiesForm()
        self.ui.setupUi(self)

        fproject = Table.tables['tasks']['project_id']
        projects = app.session.get_fk_values(fproject)

        self.ps = self.ui.projectSelect
        self.ds = self.ui.developerSelect
        self.ts = self.ui.taskSelect

        self.fillSelect(self.ps, projects)

        self.ps.currentIndexChanged.connect(self.fetchDevelopersAndTasks)

        self.readyForReport.connect(self.generateReport)
        self.readyForReport[int].connect(self.gateToGenerateReport)

        for s in (self.ds, self.ts):
            s.currentIndexChanged.connect(self.gateToGenerateReport)

        self.ps.currentIndexChanged.emit(self.ps.currentIndex())

    @QtCore.pyqtSlot(int)
    def fetchDevelopersAndTasks(self, index):
        for s in (self.ds, self.ts):
            s.currentIndexChanged.disconnect(self.gateToGenerateReport) # prevent side calls during next changes

        fdev = Table.tables['developers_distribution']['developer_username']
        ftask = Table.tables['tasks_dependencies']['task_id']
        generic_getters = (app.session.get_fk_values,) * 2
        specific_getters = (app.session.get_available_developers, app.session.get_available_tasks_for_project)
        selects = (self.ui.developerSelect, self.ui.taskSelect)
        fields = (fdev, ftask)
        for select, generic, specific, field in zip(selects, generic_getters, specific_getters, fields):
            self.fillDependedSelect(select, generic, specific, field, index)

        for s in (self.ds, self.ts):
            s.currentIndexChanged.connect(self.gateToGenerateReport)

        self.readyForReport.emit()

    def fillDependedSelect(self, select, generic_getter, specific_getter, fk_field, index):
        data = select.itemData(select.currentIndex())
        select.clear()
        if index == 0:
            keyvals = generic_getter(fk_field)
        else:
            project_id = self.ui.projectSelect.itemData(index)
            keyvals = specific_getter(project_id)
        self.fillSelect(select, keyvals)
        i = select.findData(data) # try to restore previous value
        if i != -1:
            select.setCurrentIndex(i)

    def fillSelect(self, select, keyvals):
        select.addItem('All', 0)
        keyvals = keyvals or () # in a case if keyvals are None
        for key, value in keyvals:
            select.addItem(value, key)

    @QtCore.pyqtSlot(int)
    def gateToGenerateReport(self, index):
        return self.generateReport()

    def getSelectData(self, select):
        if select.currentIndex() == 0:
            return None
        else:
            return select.itemData(select.currentIndex())

    def updateTable(self):
        return self.generateReport()

    @QtCore.pyqtSlot()
    def generateReport(self):
        project_id = self.getSelectData(self.ps)
        developer_username = self.getSelectData(self.ds)
        task_id = self.getSelectData(self.ts)
        values = app.grant.get_activities_report(project_id, developer_username, task_id)
        table = self.ui.activitiesTable
        table.clearContents()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(('Project', 'Developer', 'Task', 'Hours'))

        rows = len(values)
        table.setRowCount(rows)
        totalHours = 0
        for i, record in enumerate(values):
            totalHours += record[-1]
            for j, val in enumerate(record):
                item = QtGui.QTableWidgetItem(str(val))
                item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
                table.setItem(i, j, item)

        self.setWindowTitle('Activities, total hours: {0}'.format(totalHours))

# Somehow generate a report, what a pain the ass 

