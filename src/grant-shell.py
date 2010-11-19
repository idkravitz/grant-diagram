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

def parse_options():
    parser = optparse.OptionParser(usage='grant-shell.py [options]')
    parser.add_option("-d", "--database", dest="dbname", help="path to database", metavar="FILE")
    return parser.parse_args()

def main():
    (options, args) = parse_options()
    grant_args = {}
    if options.dbname: grant_args['dbname'] = options.dbname
    grant = libdb.Grant(echo=True, **grant_args)
    return 0

if __name__ == '__main__':
    sys.exit(main())
