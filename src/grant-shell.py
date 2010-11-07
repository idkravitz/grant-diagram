#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Grant diagram manipulation program
task is located at http://iexperts.ru/files/task2010.rar

This is a command-line interface
"""

import sys
import libdb

def main():
    connection = libdb.connect_database('test')
    return 0

if __name__ == '__main__':
    sys.exit(main())
