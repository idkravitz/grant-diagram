#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Grant diagram project management tool
task is located at http://iexperts.ru/files/task2010.rar

This is an entry point for GUI interface on PyQt
"""

import sys
from PyQt4 import QtGui

def main():
    app = QtGui.QApplication(sys.argv)

    widget = QtGui.QWidget()
    widget.resize(250, 150)
    widget.setWindowTitle('simple')
    widget.show()

    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())
