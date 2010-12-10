#!/usr/bin/env python3

import os
import re
import sys
import glob
import optparse
from os.path import join

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.normpath(join(CURRENT_PATH, "../src/"))

if SRC_PATH not in sys.path:
    sys.path.append(SRC_PATH)

from grant_shell import Interpreter

def error(message):
    print(message)
    return 1

def obtain_streams(filename):
    tf = open(filename, 'r')
    match = re.match(r"\s*include\s*<(.+)>\s*$", tf.readline())
    if match:
        return obtain_streams(match.groups(1)[0]) + [tf]
    else:
        tf.seek(0)
        return [tf]

def compare(testname):
    return os.path.exists(testname + '.ans') and open(testname + '.ans', 'r').read() == open(testname + '.out', 'r').read()

def launch(filename, options):
    streams = obtain_streams(filename)
    basename = os.path.splitext(filename)[0]
    try:
        oldout = sys.stdout
        with open(basename + ".out", "w") as sys.stdout:
            interpreter = Interpreter(streams=streams)
            interpreter.run()
    finally:
        sys.stdout = oldout
        interpreter.grant.db.clear()
    if options.debug:
        print(open(basename + ".out", "r").read())
    print('Test {0} {1}'.format('passed' if compare(basename) else 'failed', format(filename)))

def main():
    parser = optparse.OptionParser(usage='test.py [test(s)]')
    boolean_options = {
        'verbose': 'show successful tests',
        'debug': 'show tests output (includes --verbose)',
        'interactive': 'interactively decide what to do with failed tests'
    }
    for option, description in boolean_options.items():
        parser.add_option('-' + option[0], '--' + option, action='store_true', dest=option,
            default=False, help=description)
    try:
        (options, args) = parser.parse_args()
    except optparse.OptionError as e:
        return error(e.msg)
    for arg in args:
        if not os.path.exists(arg):
            return error('Path not found: {0}'.format(arg))
        if os.path.isdir(arg):
            for dirpath, dirnames, filenames in os.walk(arg):
                for test in glob.iglob(os.path.join(dirpath, '*.tst')):
                    launch(test, options)
        else:
            launch(arg, options)


if __name__ == '__main__':
    sys.exit(main())
