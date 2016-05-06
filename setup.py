#!/usr/bin/env python
from setuptools import setup

with open('requirements.txt') as reqs:
    requirements = filter(lambda s: s!='',
                          map(lambda s: s.strip(), reqs))

setup(name='LoadContracts',
      version='1.0',
      description='Uploads Serpent Dapps onto the Ethereum network',
      author='ChrisCalderon',
      author_email='calderon.christian760@gmail.com',
      packages=['load_contracts'],
      install_requires=requirements)
