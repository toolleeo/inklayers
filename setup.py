#!/usr/bin/env python

from setuptools import setup

exec(open('inklayers/version.py').read())
setup(
    name='inklayers',
    version=__version__
)
