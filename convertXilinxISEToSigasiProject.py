#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    :copyright: (c) 2008-2013 Sigasi
    :license: BSD, see LICENSE for more details.
"""

from optparse import OptionParser
import os
import platform
import subprocess
import csv
import xml.etree.ElementTree as ET

from SigasiProjectCreator import SigasiProjectCreator

def parse_xilinx_file(xilinx_file):
    entries = dict()
    tree = ET.parse(xilinx_file)
    root = tree.getroot()

    SCHEMA = '{http://www.xilinx.com/XMLSchema}'

    for f in root.findall('*/' + SCHEMA + 'file'):
        if SCHEMA + 'type' in f.attrib:
            type = f.attrib[SCHEMA + 'type']
            if type == 'FILE_VHDL':
                name = f.attrib[SCHEMA + 'name']
                lib = f.find(SCHEMA + 'library')
                library = lib.attrib[SCHEMA + 'name'] if (lib != None) else "work"
                entries[name] = library

    return entries

def main():
    usage = """usage: %prog project-name Xilinx-file [destination]

destination is the current directory by default
example: %prog MyProjectName project.xise
"""
    parser = OptionParser(usage=usage)
    (options, args) = parser.parse_args()

    if len (args) < 2:
        parser.error("incorrect number of arguments")

    project_name = args[0]
    xilinx_file = args[1]

    destination = os.getcwd()
    if len (args) > 2:
        destination = args[2]
        if not os.path.isdir(destination):
            parser.error("destination has to be a folder")

    entries = parse_xilinx_file(xilinx_file)

    print entries

    def getParts(pth):
        parts = []
        while True:
            pth, last = os.path.split(pth)
            if not last:
                break
            parts.append(last)
        return parts

    sigasProjectFileCreator = SigasiProjectCreator(project_name)
    sigasProjectFileCreator.unmap("/")

    linkedFolders = dict()
    for path, library in entries.iteritems():
        abs_destination = os.path.abspath(destination)
        abs_path = os.path.abspath(path)
        relativePath = os.path.relpath(abs_path, abs_destination)
        if (not relativePath.startswith("..")):
            sigasProjectFileCreator.add_mapping(relativePath, library)
        else:
            common_prefix = os.path.commonprefix([abs_path,abs_destination])
            eclipse_path = os.path.relpath(abs_path,common_prefix)
            directoryName = getParts(eclipse_path)[-1]
            target = os.path.join(common_prefix,directoryName)

            linkedFolders[directoryName] = target

            sigasProjectFileCreator.add_mapping(eclipse_path, library)

    # adding custom items to libraries.
    # sigasProjectFileCreator.add_unisim("C:/xilinx/14.5/ISE_DS/ISE/vhdl/src/unisims")
    # sigasProjectFileCreator.add_unimacro("C:/xilinx/14.5/ISE_DS/ISE/vhdl/src/unimacro")

    def runningInCygWin():
        return platform.system().startswith("CYGWIN")

    def convertCygwinPath(cygwinPath):
        cygwin_process = subprocess.Popen(['/usr/bin/cygpath', '--windows', cygwinPath], stdout=subprocess.PIPE)
        location = cygwin_process.communicate()[0].rstrip()
        location = location.replace('\\','/')
        return location

    for folder, location in linkedFolders.iteritems():
        if runningInCygWin():
            location = convertCygwinPath(location)
        sigasProjectFileCreator.add_link(folder, location, 2)

    sigasProjectFileCreator.write(destination)

if __name__ == '__main__':
    main()
