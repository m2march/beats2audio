#!/usr/bin/env python
import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

def parse_requirements(filename):
    """Load requirements from a pip requirements file."""
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not
            line.startswith("#")]

setup(name='m2-beats2audio',
      version='0.9',
      description='Library for producing audios from beats',
      long_description=README,
      long_description_content_type='text/markdown',
      url='https://github.com/m2march/beats2audio',
      author='Martin "March" Miguel',
      author_email='m2.march@gmail.com',
      packages=['m2', 'm2.beats2audio'],
      namespace_packages=['m2'],
      entry_points={
          'console_scripts': ['beats2audio=m2.beats2audio.cli:main']
      },
      include_package_data=True,
      install_requires=parse_requirements('requirements.txt'),
      license='MIT',
)
