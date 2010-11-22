#!/usr/bin/env python

from distutils.core import setup

from industrialise._version import VERSION

setup(name='Industrialise',
      version=VERSION,
      description='lxml.html-powered web automation',
      author='Rob Weir',
      author_email='rweir@ertius.org',
      url='http://ertius.org/code/industrialise/',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Testing',
        ],
      requires=['lxml', 'wsgi_intercept'],
      packages=['industrialise', 'industrialise.tests'],
     )
