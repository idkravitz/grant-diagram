#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Grant diagram project management tool
task is located at http://iexperts.ru/files/task2010.rar

This is a command-line interface
'''

import sys
import libdb
import optparse
import sys

def parse_options():
    parser = optparse.OptionParser(usage='grant-shell.py [options]')
    parser.add_option('-d', '--database', dest='dbname', help='path to database', metavar='FILE')
    parser.add_option('-f', '--file', dest='file', help='file to read commands from[default: stdin]',
        metavar='FILE', default='-')
    return parser.parse_args()

class Interpreter:
    UNSESSIONED = set({ 'login' })
    EMPTY = set({ 'add_company', 'add_developer' })
    def __init__(self, filename, grant):
        if filename == '-':
            self.stream = sys.stdin
        else:
            self.stream = open(filename, 'r')
        self.grant = grant
        self.session = None
        if not self.grant.has_admins():
            ans = input("Your database has no admins, want to create one[y,n]")
            if ans.lower() in set({ 'yes', 'y'}):
                print('yep')

    def readline(self):
        return self.stream.readline().rstrip()

    def run(self):
        line = self.readline()
        while len(line):
            self.interprete(line)
            line = self.readline()

    def interprete(self, line):
        atoms = line.split(' ')
        command = atoms[0]


def main():
    (options, args) = parse_options()
    grant_args = {}
    if options.dbname: grant_args['dbname'] = options.dbname
    interpreter = Interpreter(options.file, libdb.Grant(echo=True, **grant_args))
    interpreter.run()
    print("Bye!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
