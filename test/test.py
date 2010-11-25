#!/usr/bin/env python3
import os
import sys
from os.path import join
import glob

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.normpath(os.path.join(CURRENT_PATH, "../src/"))

if SRC_PATH not in sys.path:
    sys.path.append(SRC_PATH)

import grant_shell
import libdb

def main():
    pass


if __name__ == '__main__':
    sys.exit(main())
