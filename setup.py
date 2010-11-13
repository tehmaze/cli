from setuptools import setup, find_packages
from cli.version import version

setup(
    name         = 'cli',
    version      = version(),
    author       = 'Wijnand Modderman-Lenstra',
    author_email = 'maze@pyth0n.org',
    description  = 'Command Line Interface',
    long_description = file('README.rst').read(),
    license      = 'MIT',
    keywords     = 'cli command line',
    packages     = ['cli'],
)

