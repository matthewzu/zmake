#!/usr/bin/env python
#-*- coding:utf-8 -*-

import setuptools
import os

with open("README.md","r") as fd:
    long_description = fd.read()

setuptools.setup(
    name                            = 'zmake',
    version                         = '0.1.1',
    author                          = 'Matthew Zu',
    author_email                    = 'xiaofeng_zu@163.com',
    keywords                        = ['make', 'ninja-build', 'yaml', 'kconfig'],
    description                     = 'A Make/ninja-build file generator from Kconfig/YAML config files',
    long_description                = long_description,
    long_description_content_type   = 'text/markdown',
    url                             = 'https://github.com/matthewzu/zmake',
    packages                        = setuptools.find_packages(),
    install_requires                = ['kconfiglib', 'pyyaml'],
    classifiers                     = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: OS Independent",
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
    ],
    entry_points                    = {
        'console_scripts': [
            'zmake      = zmake.cli:generator',
            'zmake-demo = zmake.cli:demo_create',
        ],
    },
    package_data                    = {
        'zmake': ['../README-cn.md', 'demo/*', 'demo/main/*', 'demo/mod1/*', 'demo/mod1/mod11/*', 'demo/mod1/mod11/source/*',
            'demo/mod1/mod11/include/mod11/*', 'demo/mod1/mod12/*', 'demo/mod2/*', 'demo/mod2/h/*'],
    },
)