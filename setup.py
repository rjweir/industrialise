#!/usr/bin/env python

from setuptools import setup

from industrialise import __version__

setup(name='Industrialise',
      version=__version__,
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
