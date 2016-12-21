#!/usr/bin/env python

from setuptools import setup

setup(name='beats2audio',
      version='0.1',
      description='Script for producing audio from .beats files',
      author='Martin "March" Miguel',
      author_email='m2.march@gmail.com',
      packages=['scripts'],
      package_data={
          'scripts': ['click.mp3']
      },
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
      entry_points={
          'console_scripts': [
              'beats2audio=scripts.beats2audio:__main__'
          ]
      }
      )
