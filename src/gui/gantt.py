from PyQt4 import QtGui, QtCore
from designer.gantt_form import Ui_Gantt

class GanttForm(QtGui.QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self.ui = Ui_Gantt()
        self.ui.setupUi(self)
        self.ui.webView.setHtml(html)
