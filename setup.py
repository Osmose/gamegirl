#!/usr/bin/env python
import codecs
import os
import re
from setuptools import setup, find_packages


def read(*parts):
    return codecs.open(os.path.join(os.path.dirname(__file__), *parts), encoding='utf8').read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name='gamegirl',
    description='Gameboy emulator.',
    long_description=read('README.rst'),
    version=find_version('gamegirl/__init__.py'),
    packages=find_packages(),
    author='Michael Kelly',
    author_email='me@mkelly.me',
    url='https://github.com/Osmose/gamegirl',
    license='MIT',
    install_requires=['docopt>=0.6'],
    include_package_data=True,
    entry_points={
      'console_scripts':[
          'gamegirl = gamegirl.cmd:main'
      ]
   }
)
