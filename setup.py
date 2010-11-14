#!/usr/bin/env python

from distutils.core import setup

from industrialise._version import VERSION

setup(name='Industrialise',
      version=VERSION,
      description='lxml.html-powered web automation',
      author='Rob Weir',
      author_email='rweir@ertius.org',
      url='http://ertius.org/code/industrialise/',
      packages=['industrialise', 'industrialise.tests'],
     )
