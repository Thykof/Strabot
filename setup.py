import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


import pytest


class PyTest(TestCommand):
    def run_tests(self):
        errno = pytest.main(['-vv'])
        sys.exit(errno)


def read(filename):
    with open(filename, 'r') as myfile:
        return myfile.read()


setup(
    name='Strabot',
    version='1.0',
    description='Crypto trading bot',
    author='Nathan Seva',
    author_email='thykof@protonmail.ch',
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    license="GNU GPL v3",
    packages=find_packages(),
    cmdclass={'test': PyTest},
    install_requires=read('requirements.txt').split(),
    tests_require=['pytest'],
    extras_require={
        'testing': ['pytest', 'coverage']
    }
)
