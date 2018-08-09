#!/usr/bin/env python3

""" PYTHON3 - Setup for parkingmonitor. """

from setuptools import setup

def readme():
    """ README """
    with open('README.rst') as freader:
        return freader.read()

setup(name='parkingmonitor',
      version='0.1',
      description='Parking Monitor library for SUMO via TraCI.',
      url='http://github.com/lcodeca/parkingmonitor',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Programming Language :: Python :: 3 :: Only',
          'Intended Audience :: Science/Research',
          'Topic :: Scientific/Engineering',
      ],
      author='Lara Codeca',
      author_email='lara.codeca@gmail.com',
      license='GPL.v3',
      packages=['parkingmonitor'],
      install_requires=[],
      include_package_data=True,
      zip_safe=False,
      test_suite='nose.collector',
      tests_require=['nose'])
