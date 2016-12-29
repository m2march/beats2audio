#!/usr/bin/env python

from setuptools import setup

setup(name='beats2audio',
      version='0.1',
      description='Library for producing audios from beats',
      author='Martin "March" Miguel',
      author_email='m2.march@gmail.com',
      packages=['m2.beats2audio'],
      namespace_package=['m2'],
      scripts=['scripts/beats2audio'],
      package_data={
          'm2.beats2audio': ['m2/beats2audio/click.mp3']
      },
      install_requires=[
          'pydub',
          'python-gflags',
          'python-magic',
          'numpy',
      ],
      )
