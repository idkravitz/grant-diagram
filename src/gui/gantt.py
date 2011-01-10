from PyQt4 import QtGui, QtCore

from designer.gantt_form import Ui_Gantt
from gui.ganttgenerator import GanttGenerator
from grant_core.init_tables import Table

class GanttForm(QtGui.QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self.ui = Ui_Gantt()
        self.ui.setupUi(self)

        fproject = Table.tables['tasks']['project_id']
        projects = app.session.get_fk_values(fproject) or ()
        ps = self.ui.projectSelect
        for key, value in projects:
            ps.addItem(value, key)
        ps.currentIndexChanged.connect(self.drawGantt)
        self.ps = ps
        ps.currentIndexChanged.emit(ps.currentIndex())

    def updateTable(self):
        self.drawGantt(0)

    def drawGantt(self, index):
        gen = GanttGenerator(self.ps.itemData(index))
        self.ui.webView.setHtml(gen.dumpGantt())

