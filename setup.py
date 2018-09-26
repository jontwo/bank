#!/usr/bin/env python

import os
import re
from setuptools import setup

init_py = open(os.path.join('bank', '__init__.py')).read()
info = dict(re.findall("__([a-z_]+)__\s*=\s*'([^']+)'", init_py))

setup(
    name='bank',
    version=info['version'],
    description='Bank statement parsing utility',
    packages=['bank'],
    include_package_data=True,
    install_requires=['argparse', 'pandas', 'six', 'xlrd>=0.9.0'],
    test_suite='test_bank',
    zip_safe=False,
    author=info['author'],
    author_email=info['author_email'],
    url='https://github.com/jontwo/bank',
    entry_points={
        'console_scripts': [
            'bank = bank:main'
        ]
    },
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 2.7',
        'Topic :: Office/Business :: Financial',
    ]
)
