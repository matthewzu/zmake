"""
    zmake.cli
    ~~~~~~~~~~

    Supply command interface.

    :copyright: (c) 2023 by Matthew Zu.
    :license: Mozilla Public License, Version 2.0, see LICENSE for more details.
"""

import os, shutil, argparse, logging
import zmake.core
import zmake.kconfig
import zmake.yaml
import zmake.generator

def generator():
    parser = argparse.ArgumentParser(description = "ZMake build Generator")

    parser.add_argument('-v', '--version',
                        action  = 'version', version = zmake.core.ver(),
                        help    = 'show version')
    parser.add_argument('-V', '--verbose',
                        default = False, action = 'store_true',
                        help    = 'enable verbose output')
    parser.add_argument("-k", "--kconfig",
                        default = '', metavar = '"Kconfig file"',
                        help    = 'specify Kconfig root configuration file, "Kconfig" by default')
    parser.add_argument("-y", "--yaml",
                        default = '', metavar = '"YAML file"',
                        help    = 'specify YAML root configuration file, "top.yml" by default')
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-d", "--defconfig",
                        default = '', metavar = '"defconfig file"',
                        help    = 'specify defconfig file')
    group.add_argument("-m", "--menuconfig",
                        default = '', metavar = '"Source Code Path"',
                        help    = 'enable menuconfig method, \nused after project created ONLY')

    parser.add_argument("-g", "--generator",
                        default = zmake.core.PRJ_GEN_TYPE_MAKE, choices = zmake.core.PRJ_GEN_TYPES,
                        help    = 'build generator, "make" by default')
    parser.add_argument("project",
                        help    ='project path')

    args = parser.parse_args()

    zmake.core.init(os.path.abspath('.'), os.path.abspath(args.project), args.generator, args.verbose)

    if args.defconfig != '':
        defconfig   = os.path.abspath(args.defconfig)
    else:
        defconfig   = ""

    if args.menuconfig != '':
        confdir     = os.path.abspath(args.menuconfig)
    else:
        confdir     = ""

    zmake.kconfig.init(args.kconfig, defconfig, confdir)

    if args.menuconfig != '':
        zmake.kconfig.menuconfig()
    else:
        zmake.kconfig.genconfig()

    zmake.yaml.init(args.yaml)
    zmake.generator.generate()

def demo_create():
    parser = argparse.ArgumentParser(description = "ZMake demo project creator")
    parser.add_argument("path", help = 'path that demo project will be created')
    args = parser.parse_args()

    src = os.path.join(os.path.dirname(__file__), 'demo')
    print("Creating demo project in %s from %s" %(args.path, src))
    shutil.copytree(src, args.path)
