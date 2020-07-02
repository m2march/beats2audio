#!/usr/bin/env python

from setuptools import setup

setup(name='beats2audio',
      version='0.1',
      description='Library for producing audios from beats',
      author='Martin "March" Miguel',
      author_email='m2.march@gmail.com',
      packages=['m2', 'm2.beats2audio'],
      namespace_packages=['m2'],
      entry_points={
          'console_scripts': ['beats2audio=m2.beats2audio.cli:main']
      },
      package_data={
          'm2.beats2audio': ['m2/beats2audio/click.wav']
      },
      install_requires=[
          'pydub',
          'python-gflags',
          'python-magic',
          'numpy',
      ],
      )
