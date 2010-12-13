#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Grant diagram project management tool
task is located at http://iexperts.ru/files/task2010.rar

This is an entry point for GUI interface on PyQt
"""

import sys

from PyQt4 import QtGui, QtCore

from designer.mainwindow import Ui_MainWindow

class Window(QtGui.QMainWindow):
    def __init__(self):
        super(Window, self).__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

app = QtGui.QApplication(sys.argv)
tooltip = Window()
tooltip.show()
sys.exit(app.exec_())
