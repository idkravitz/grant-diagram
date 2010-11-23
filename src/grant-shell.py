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

class EmptyStream(Exception):
    pass

class TokenError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "Token error: {0}".format(self.msg)

class SynError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "Syntax error: {0}".format(self.msg)

class Tokenizer(object):
    class Token(object):
        def __init__(self, type, text, value):
            self.type = type
            self.text = text
            self.value = value

    def __init__(self, stream):
        self.stream = stream
        self.ptr = 0
        self.buffer = stream.readline()

    def getch(self, adv=True):
        if not len(self.buffer):
            raise EmptyStream()
        if self.ptr < len(self.buffer):
            ch = self.buffer[self.ptr]
            if adv: self.ptr += 1
            return ch
        else:
            self.buffer = self.stream.readline()
            self.ptr = 0
            return self.getch(adv=adv)

    def get_token(self):
        ch = self.getch()
        while ch.isspace():
            ch = self.getch()

        if ch == '"' or ch == "'":
            bnd = text = ch
            try:
                ch = self.getch()
                while ch != bnd:
                    text += ch
                    if ch == "\n":
                        raise TokenError("new line in string literal")
                    ch = self.getch()
            except EmptyStream:
                raise TokenError("EOF meet before string literal ends")
            text += ch
            return self.Token('string', text, text[1:-1])
        elif ch.isdigit():
            n = ch
            try:
                ch = self.getch()
                while ch.isdigit():
                    n += ch
                    ch = self.getch()
                self.ptr -= 1
            except EmptyStream:
                pass
            return self.Token('int', n, int(n))
        elif ch.isalpha() or ch == "_":
            identifier = ch
            try:
                ch = self.getch()
                while ch.isalpha() or ch == "_":
                    identifier += ch
                    ch = self.getch()
                self.ptr -= 1
            except EmptyStream:
                pass
            return self.Token('identifier', identifier, identifier)
        elif ch == ",":
            return self.Token('comma', ',', ',')
        elif ch == ";":
            return self.Token('semicolon', ';', ';')
        raise TokenError("unknown token {0}".format(ch))

class Parser(object):
    def __init__(self, stream):
        self.tokenizer = Tokenizer(stream)

    def parse_command(self):
        command = self.tokenizer.get_token()
        if command.type != 'identifier':
            raise SynError('command must be a valid identifier')
        try:
            args = []
            arg_token = self.tokenizer.get_token()
            while arg_token.type != 'semicolon':
                if arg_token.type not in set({'int', 'string'}):
                    raise SynError('invalid token in command args')
                args.append(arg_token.value)
                arg_token = self.tokenizer.get_token()
                if arg_token.type != 'semicolon' and arg_token.type != 'comma':
                    raise SynError('invalid token in command args')
                if arg_token.type == 'comma':
                    arg_token = self.tokenizer.get_token()
        except EmptyStream:
            raise SynError('incomplete command statement')
        return (command.value, args)

    def parse_commands(self):
        try:
            while True:
                yield self.parse_command()
        except EmptyStream:
            return
        except (SynError, TokenError) as e:
            print(e)

class Interpreter:
    def __init__(self, filename, grant):
        if filename == '-':
            self.stream = sys.stdin
        else:
            self.stream = open(filename, 'r')
        self.grant = grant
        self.parser = Parser(self.stream)
        self.session = None
        if not self.grant.has_admins():
            print("Your database has no admins, use add_company, add_developer to create one")

    def run(self):
        for command, args in self.parser.parse_commands():
            print(command)
            for arg in args:
                print("A: {0}".format(arg))

    def interprete(self, line):
        atoms = line.split(' ')
        command = atoms[0]
        if not self.has_admins():
            self.admin_create_process()

def main():
    (options, args) = parse_options()
    grant_args = {}
    if options.dbname: grant_args['dbname'] = options.dbname
    interpreter = Interpreter(options.file, libdb.Grant(echo=True, **grant_args))
    interpreter.run()
    print("\nBye!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
