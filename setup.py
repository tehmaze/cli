from setuptools import setup, find_packages

setup(
    name         = 'cli',
    version      = '0.0.1',
    author       = 'Wijnand Modderman-Lenstra',
    author_email = 'maze@pyth0n.org',
    description  = 'Command Line Interface',
    long_description = file('README.rst').read(),
    license      = 'MIT',
    keywords     = 'cli command line',
    packages     = ['cli'],
)

