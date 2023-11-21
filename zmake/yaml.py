"""
    zmake.yaml
    ~~~~~~~~~~

    Supply YAML related functions.

    :copyright: (c) 2023 by Matthew Zu.
    :license: Apache License, Version 2.0, see LICENSE for more details.
"""

import os, pprint, yaml, logging

from . import ZMAKE_DBG_FMT, _SRC_TREE, _zmake_exception

logging.basicConfig(level = logging.DEBUG, format = ZMAKE_DBG_FMT)

# yaml

_YAML_FILES         = []
_YAML_DATA          = {}

def _yml_file_load(path: str):
    """Initialize YAML library.

    path: name of YAML root configuration file, optional.
    """

    global _YAML_FILES
    global _YAML_DATA

    real_path = os.path.join(_SRC_TREE, path)
    if not os.path.isfile(real_path):
        raise _zmake_exception("yaml load: %s NOT exist" %real_path)

    logging.debug("open %s", real_path)
    fd = open(real_path, 'r', encoding='utf-8')

    logging.debug("load %s", real_path)
    data = yaml.safe_load(fd.read())
    if data == None:
        raise _zmake_exception("%s is empty" %real_path)

    fd.close()
    _YAML_FILES += os.path.abspath(real_path)
    _YAML_DATA  = {**_YAML_DATA, **data}

    if 'includes' not in data:
        return

    if data['includes'] == []:
        return

    for file in data['includes']:
        _yml_file_load(file)

def init(path = ''):
    """Initialize YAML library.

    path: name of YAML root configuration file, 'top.yml' by default, optional.
    """

    if path == '':
        path = 'top.yml'

    _yml_file_load(path)

def data():
    """Return YAML data
    """

    return _YAML_DATA