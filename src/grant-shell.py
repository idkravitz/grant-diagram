#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Grant diagram project management tool
task is located at http://iexperts.ru/files/task2010.rar

This is a command-line interface
"""

import sys
import libdb
import optparse

def main():
    parser = optparse.OptionParser(usage='grant-shell.py [options]')
    grant = libdb.Grant(echo=True)
    return 0

if __name__ == '__main__':
    sys.exit(main())
