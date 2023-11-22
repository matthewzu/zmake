"""
    zmake.kconfig
    ~~~~~~~~~~

    Supply Kconfig related functions.

    :copyright: (c) 2023 by Matthew Zu.
    :license: Mozilla Public License, Version 2.0, see LICENSE for more details.
"""

import os, re, subprocess, logging
import zmake.core

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
    #    raise zmake.core.exception("Kconfig could NOT be called for Windows now")

    zmake.core.LOGGER.info("Kconfig initializing...")
    zmake.core.LOGGER.debug("\troot configuration file: %s", _KCONFIG_ROOT)
    zmake.core.LOGGER.debug("\tdefconfig file: %s", defconfig)

    if confdir != '':
        zmake.core.SRC_TREE = confdir

    zmake.core.LOGGER.info("set 'srctree' to %s", zmake.core.SRC_TREE)
    os.environ['srctree'] = zmake.core.SRC_TREE

    if defconfig != '':
        if not os.path.exists(defconfig):
            raise zmake.core.exception("%s is invalid path" %defconfig)
        else:
            _KCONFIG_DEFCONFIG = os.path.abspath(defconfig)

    _KCONFIG_CONFIG_PATH = os.path.join(zmake.core.PRJ_DIR, _KCONFIG_CONFIG_PATH)
    zmake.core.dir_create(_KCONFIG_CONFIG_PATH)

    _KCONFIG_CONFIG = os.path.join(_KCONFIG_CONFIG_PATH, _KCONFIG_CONFIG)
    _KCONFIG_HDR = os.path.join(_KCONFIG_CONFIG_PATH, _KCONFIG_HDR)

def _parse():
    global _KCONFIG_MODULE_OPTIONS

    if not os.path.isfile(_KCONFIG_CONFIG):
        raise zmake.core.exception("yaml load: %s NOT exist" %_KCONFIG_CONFIG)

    pattern = re.compile('^CONFIG_(\S*)+=y\n')
    zmake.core.LOGGER.info("parsing %s...", _KCONFIG_CONFIG)
    with open(_KCONFIG_CONFIG, 'r', encoding='utf-8') as file:
        for line in file:
            temp = pattern.search(line)
            if temp != None:
                opt = re.sub(r"^CONFIG_(\S+)+=y\n", r"CONFIG_\1",line)
                zmake.core.LOGGER.debug("opt: %s", opt)
                _KCONFIG_MODULE_OPTIONS.append(opt)

def genconfig():
    """Generate configuration file(config.h and config.mk)
    """

    if _KCONFIG_DEFCONFIG == '':
        if 'KCONFIG_CONFIG' in os.environ:
            zmake.core.LOGGER.info("unset KCONFIG_CONFIG")
            os.environ.pop('KCONFIG_CONFIG')
    else:
        zmake.core.LOGGER.info("set KCONFIG_CONFIG to %s", _KCONFIG_DEFCONFIG)
        os.environ['KCONFIG_CONFIG'] = _KCONFIG_DEFCONFIG

    zmake.core.LOGGER.info("generating %s and %s ...", _KCONFIG_HDR, _KCONFIG_CONFIG)
    ret = subprocess.run(['genconfig', '--header-path', _KCONFIG_HDR, '--config-out', _KCONFIG_CONFIG, _KCONFIG_ROOT])

    if ret.returncode != 0:
        raise zmake.core.exception("failed to generate %s" %_KCONFIG_CONFIG)

    _parse()

def menuconfig():
    """trigger menuconfig to configure project and generate configuration file(config.h and config.mk)
    """

    if not os.path.isfile(_KCONFIG_CONFIG):
        raise zmake.core.exception("menuconfig method could ONLY be used after project"
            " is created and %s is existed" %_KCONFIG_CONFIG)

    zmake.core.LOGGER.info("set KCONFIG_CONFIG to %s", _KCONFIG_CONFIG)
    os.environ['KCONFIG_CONFIG'] = _KCONFIG_CONFIG

    zmake.core.LOGGER.info("execute menuconfig")
    ret = subprocess.run(['menuconfig', _KCONFIG_ROOT])

    if ret.returncode != 0:
        raise zmake.core.exception("failed to run menuconfig")

    zmake.core.LOGGER.info("generating %s and %s ...", _KCONFIG_HDR, _KCONFIG_CONFIG)
    ret = subprocess.run(['genconfig', '--header-path', _KCONFIG_HDR, '--config-out', _KCONFIG_CONFIG, _KCONFIG_ROOT])

    if ret.returncode != 0:
        raise zmake.core.exception("failed to generate %s" %_KCONFIG_CONFIG)

    _parse()

def options_find(opt):
    """Check if the option is valid for library/application
        opt: string, option name
    """

    if not isinstance(opt, str):
        raise zmake.core.exception("opt(%s) must be str type for library/appliation" %opt)

    if opt == "":
        return True
    else:
        return opt in _KCONFIG_MODULE_OPTIONS
