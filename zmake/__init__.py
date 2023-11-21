import logging

# logging

ZMAKE_DBG_FMT = '%(levelname)s[%(asctime)s]:%(message)s'

# project

_SRC_TREE   = ''    # source code path
_PRJ_DIR    = ''    # project path

# Excpetion Class

class _zmake_exception(Exception):
    def __init__(self, message):
        self.message = message

