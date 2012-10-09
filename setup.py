#!/usr/bin/env python
# -*- coding: utf-8
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

install_requires = []
if sys.version_info < (2, 7):
    install_requires.append('argparse')

import fragments

setup(
    name='fragments',
    version='.'.join(map(str, fragments.__version__)),
    description='tool for diff-based templating / fragmentation control',
    long_description=open('README.md').read(),
    author='Matt Chisholm',
    author_email='matt-fragments@theory.org',
    url='https://github.com/glyphobet/fragments',
    packages= ['fragments',],
    install_requires=install_requires,
    entry_points = {
        'console_scripts': [
            'fragments = fragments.commands:_main',
        ],
    },
    data_files=[('share/fragments', ['README.md', 'bash_completion', 'LICENSE.txt'])],
    license='BSD License',
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
    ),
)
