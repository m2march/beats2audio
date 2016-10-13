#!/usr/bin/env python

from setuptools import setup

setup(name='tht',
      version='0.1',
      description='Tactus Hypothesis Tracking Module',
      author='Martin "March" Miguel',
      author_email='m2.march@gmail.com',
      packages=[],
      install_requires=[
          'pydub',
          'python-gflags',
          'python-magic',
          'numpy',
          'tht'
      ],
      dependency_links=[
          '../tht'
      ],
      scripts=['scripts/beats2audio.py']
      )
