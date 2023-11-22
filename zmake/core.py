"""
    zmake.core
    ~~~~~~~~~~

    Supply core functions.

    :copyright: (c) 2023 by Matthew Zu.
    :license: Mozilla Public License, Version 2.0, see LICENSE for more details.
"""

import os, logging

# project parameter

SRC_TREE   = ''    # source code path
PRJ_DIR    = ''    # project path
PRJ_GEN    = ''    # build generator
PRJ_VERB   = False # enable verbose output

# build generator type

PRJ_GEN_TYPE_MAKE  = 'make'
PRJ_GEN_TYPE_NINJA = 'ninja'
PRJ_GEN_TYPES      = ['make', 'ninja']

# logging

LOG_FILE    = 'zmake.log'
LOGGER      = None

# misc

_ZMAKE_VER = '0.1.0'

# utilities

class exception(Exception):
    """zmake_exception:
        supply more exception information.
    """

    def __init__(self, message):
        self.message = message

def ver():
    """ver:
        return zmake version string.
        e.g. "zmake 0.1"
    """

    return "ZMake %s" %_ZMAKE_VER

def dir_create(path):
    """dir_create:
        create directory specified by <path>.
    """

    if os.path.exists(path):
        return

    LOGGER.info("create %s", path)
    os.makedirs(path)

def _file_clear(path: str):
    """file_clear:
        clear file specified by <path>.
    """

    if not os.path.exists(path):
        return

    print("clear %s" %path)
    with open(path, 'w') as file:
        file.truncate(0)

def logging_init():
    """logging_init:
        initialize logging.
    """

    global LOG_FILE
    global LOGGER

    LOGGER = logging.getLogger()
    LOGGER.setLevel(logging.DEBUG)

    dir_create(PRJ_DIR)
    LOG_FILE = os.path.join(PRJ_DIR, LOG_FILE)

    file_handler    = logging.FileHandler(LOG_FILE)
    file_formatter  = logging.Formatter('%(asctime)s[%(levelname)s]:%(message)s')
    file_handler.setFormatter(file_formatter)

    console_handler     = logging.StreamHandler()
    console_formatter   = logging.Formatter('[%(levelname)s]:%(message)s')
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)

    LOGGER.addHandler(file_handler)
    LOGGER.addHandler(console_handler)

def init(src_path: str, prj_path: str, prj_gen: str, verbose: bool):
    """Initialize ZMake core library
        src_path: string, path of source code;
        prj_path: string, path of project;
        prj_gen: string, type of build generator, must be 'ninja' or 'make';
        verbose: bool, enable verbose output.
    """
    global SRC_TREE
    global PRJ_DIR
    global PRJ_GEN
    global PRJ_VERB

    if prj_gen not in PRJ_GEN_TYPES:
        raise exception("invalid build generator: %s" %prj_gen)

    SRC_TREE    = src_path
    PRJ_DIR     = prj_path
    PRJ_GEN     = prj_gen
    PRJ_VERB    = verbose

    logging_init()
    LOGGER.info("######################%s######################\n", ver())
    LOGGER.info("Core initializing...")
    LOGGER.debug("\tsource Code Path    : %s", SRC_TREE)
    LOGGER.debug("\tproject path        : %s", PRJ_DIR)
    LOGGER.debug("\tbuild generator     : %s", PRJ_GEN)
    LOGGER.debug("\tverbose             : %s", str(PRJ_VERB))
