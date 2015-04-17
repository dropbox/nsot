#!/usr/bin/env python

import os

from setuptools import setup, find_packages

execfile('nsot/version.py')

with open('requirements.txt') as requirements:
    required = requirements.read().splitlines()

package_data = {}
def get_package_data(package, base_dir):
    for dirpath, dirnames, filenames in os.walk(base_dir):
        dirpath = dirpath[len(package)+1:]  # Strip package dir
        for filename in filenames:
            package_data.setdefault(package, []).append(os.path.join(dirpath, filename))
        for dirname in dirnames:
            get_package_data(package, dirname)

get_package_data('nsot', 'nsot/static')
get_package_data('nsot', 'nsot/templates')
get_package_data('nsot', 'nsot/migrations')

kwargs = {
    'name': 'nsot',
    'version': str(__version__),
    'packages': find_packages(exclude=['tests']),
    'package_data': package_data,
    'description': 'Network Source of Truth (IP Address Management).',
    'author': 'Gary M. Josack',
    'maintainer': 'Gary M. Josack',
    'author_email': 'gary@dropbox.com',
    'maintainer_email': 'gary@dropbox.com',
    'license': 'Apache',
    'install_requires': required,
    'url': 'https://github.com/dropbox/nsot',
    'entry_points': """
        [console_scripts]
        nsot-server=nsot.util:main
    """,
    'classifiers': [
        'Programming Language :: Python',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
}

setup(**kwargs)
