#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import os
import re

VIMMODE_LINE = "# vim: ai ts=4 sts=4 et sw=4\n"


def file_needs_writing(named):
    try:
        f = open(named, 'r')
        for line in range(0, 3):
            if re.search(r'#[\s]*vim:', f.readline()): return False
        return True
    finally:
        f.close()

def vimmode_fix(named):
    f = open(named, 'r+')
    original = f.readlines()
    f.seek(0)
    if len(original) > 0 and re.search(r'#!.*bin.*python', original[0]):
        f.seek(len(original[0]))
        original = original[1:]
    f.write(VIMMODE_LINE)
    f.writelines(original)
    f.close()
    print "vimmode fixed for: %s" % named

def run():
    for dirpath, _, files in os.walk(os.path.dirname(__file__)):
        for file in [file for file in files if file[-3:] == '.py']:
            abs_file = os.path.join(dirpath, file)
            if file_needs_writing(abs_file):
                vimmode_fix(abs_file)

if __name__ == '__main__':
    run()
