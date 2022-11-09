# -*- coding: utf-8 -*-
import sys
from fabric.colors import red, green, cyan, blue, yellow


def print_error(msg, stop=True):
    print(red(" ✘   %s\n\n ✘   Task failed. Fix issues list above.\n" % msg))
    if stop:
        sys.exit()


def print_warning(msg):
    print(yellow(" !   %s ..." % msg))


def print_start(msg):
    print(cyan("==>> %s ..." % msg))


def print_done(msg):
    print(green(" ✔   %s" % msg))


def print_info(msg):
    print(blue(" ☞   %s" % msg))
