"""
    zmake.kconfig
    ~~~~~~~~~~

    Supply Kconfig related functions.

    :copyright: (c) 2023 by Matthew Zu.
    :license: Apache License, Version 2.0, see LICENSE for more details.
"""

import os, re, subprocess, logging
from . import ZMAKE_DBG_FMT, _SRC_TREE, _PRJ_DIR, _zmake_exception

logging.basicConfig(level = logging.DEBUG, format = ZMAKE_DBG_FMT)

# Kconfig

_KCONFIG_ROOT           = "Kconfig"
_KCONFIG_DEFCONFIG      = ''
_KCONFIG_CONFIG_PATH    = "config"
_KCONFIG_HDR            = 'config.h'
_KCONFIG_CONFIG         = 'config.mk'
_KCONFIG_MODULE_OPTIONS = []    # CONFIG_XXX for modules

# Kconfig functions

def init(kconfig_root = '', defconfig = '', confdir = ''):
    """Initialize ZMake Kconfig library
        defconfig: string, path of Kconfig defconfig file, optional;
        confdir: string, path of Kconfig config files, optional.
    """

    global _SRC_TREE
    global _KCONFIG_ROOT
    global _KCONFIG_DEFCONFIG
    global _KCONFIG_CONFIG_PATH
    global _KCONFIG_CONFIG
    global _KCONFIG_HDR

    if kconfig_root == "":
        _KCONFIG_ROOT = "Kconfig"
    else:
        _KCONFIG_ROOT = kconfig_root

    #if os.name == 'nt':
    #    raise _zmake_exception("Kconfig could NOT be called for Windows now")

    logging.info("Kconfig root configuration file: %s", _KCONFIG_ROOT)
    logging.info("Kconfig defconfig file: %s", defconfig)

    if confdir != '':
        _SRC_TREE = confdir

    logging.info("Source code path: %s", _SRC_TREE)
    logging.info("set 'srctree' to %s", _SRC_TREE)
    os.environ['srctree'] = _SRC_TREE

    if defconfig != '':
        if not os.path.exists(defconfig):
            raise _zmake_exception("%s is invalid path" %defconfig)
        else:
            _KCONFIG_DEFCONFIG = os.path.abspath(defconfig)

    _KCONFIG_CONFIG_PATH = os.path.join(_PRJ_DIR, _KCONFIG_CONFIG_PATH)
    logging.info("create Kconfig output directory %s", _KCONFIG_CONFIG_PATH)
    if os.path.exists(_KCONFIG_CONFIG_PATH):
        return

    logging.info("create %s", _KCONFIG_CONFIG_PATH)
    os.makedirs(_KCONFIG_CONFIG_PATH)

    _KCONFIG_CONFIG = os.path.join(_KCONFIG_CONFIG_PATH, _KCONFIG_CONFIG)
    _KCONFIG_HDR = os.path.join(_KCONFIG_CONFIG_PATH, _KCONFIG_HDR)

def _parse():
    global _KCONFIG_MODULE_OPTIONS

    if not os.path.isfile(_KCONFIG_CONFIG):
        raise _zmake_exception("yaml load: %s NOT exist" %_KCONFIG_CONFIG)

    pattern = re.compile('^CONFIG_(\S*)+=y\n')
    logging.info("parse %s", _KCONFIG_CONFIG)
    with open(_KCONFIG_CONFIG, 'r', encoding='utf-8') as file:
        for line in file:
            temp = pattern.search(line)
            if temp != None:
                opt = re.sub(r"^CONFIG_(\S+)+=y\n", r"CONFIG_\1",line)
                logging.debug("opt: %s", opt)
                _KCONFIG_MODULE_OPTIONS.append(opt)

def genconfig():
    """Generate configuration file(config.h and config.mk)
    """

    if _KCONFIG_DEFCONFIG == '':
        if 'KCONFIG_CONFIG' in os.environ:
            logging.info("unset KCONFIG_CONFIG")
            os.environ.pop('KCONFIG_CONFIG')
    else:
        logging.info("set KCONFIG_CONFIG to %s", _KCONFIG_DEFCONFIG)
        os.environ['KCONFIG_CONFIG'] = _KCONFIG_DEFCONFIG

    logging.info("generate %s and %s", _KCONFIG_HDR, _KCONFIG_CONFIG)
    ret = subprocess.run(['genconfig', '--header-path', _KCONFIG_HDR, '--config-out', _KCONFIG_CONFIG, _KCONFIG_ROOT])

    if ret.returncode != 0:
        raise _zmake_exception("failed to generate %s" %_KCONFIG_CONFIG)

    _parse()

def menuconfig():
    """trigger menuconfig to configure project and generate configuration file(config.h and config.mk)
    """

    if not os.path.isfile(_KCONFIG_CONFIG):
        raise _zmake_exception("menuconfig method could ONLY be used after project"
            " is created and %s is existed" %_KCONFIG_CONFIG)

    logging.info("set KCONFIG_CONFIG to %s", _KCONFIG_CONFIG)
    os.environ['KCONFIG_CONFIG'] = _KCONFIG_CONFIG

    logging.info("execute menuconfig")
    ret = subprocess.run(['menuconfig', _KCONFIG_ROOT])

    if ret.returncode != 0:
        raise _zmake_exception("failed to run menuconfig")

    logging.info("generate %s and %s", _KCONFIG_HDR, _KCONFIG_CONFIG)
    ret = subprocess.run(['genconfig', '--header-path', _KCONFIG_HDR, '--config-out', _KCONFIG_CONFIG, _KCONFIG_ROOT])

    if ret.returncode != 0:
        raise _zmake_exception("failed to generate %s" %_KCONFIG_CONFIG)

    _parse()

def options_find(opt):
    """Check if the option is valid for library/application
        opt: string, option name
    """

    if not isinstance(opt, str):
        raise _zmake_exception("opt(%s) must be str type for library/appliation" %opt)

    if opt == "":
        return True
    else:
        return opt in _KCONFIG_MODULE_OPTIONS
