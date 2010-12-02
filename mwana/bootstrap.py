#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
# bootstrap.py
# Bootstrap and setup a virtualenv with the specified requirements.txt
import os
import sys
import shutil
import subprocess
from optparse import OptionParser


usage = """usage: %prog [options]"""
parser = OptionParser(usage=usage)
parser.add_option("-c", "--clear", dest="clear", action="store_true",
                  help="clear out existing virtualenv")


def main():
    if "VIRTUAL_ENV" not in os.environ:
        sys.stderr.write("$VIRTUAL_ENV not found.\n\n")
        parser.print_usage()
        sys.exit(-1)
    (options, pos_args) = parser.parse_args()
    virtualenv = os.environ["VIRTUAL_ENV"]
    if options.clear:
        subprocess.call(["virtualenv", "--clear", "--distribute",
                         virtualenv])
    file_path = os.path.dirname(__file__)
    os.chdir(os.path.join(file_path, 'requirements'))
    for file_name in ['libs.txt', 'pygsm.txt']:
        subprocess.call(["pip", "install", "-E", virtualenv, "--no-deps",
                         "--requirement", file_name])


if __name__ == "__main__":
    main()
    sys.exit(0)
