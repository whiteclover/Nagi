from setuptools import setup
import sys
from nagi import version

setup(
    name = 'nagi',
    version = version,
    author = "Thomas Huang",
    author_email='lyanghwy@gmail.com',
    description = "Leaderboard System",
    license = "GPL",
    keywords = "Leaderboard",
    url='https://github.com/thomashuang/Nagi',
    long_description=open('README.rst').read(),
    packages = ['nagi', 'nagi.model', 'nagi.thing'],
    install_requires = ['setuptools', 'MySQL-python'],
    classifiers=(
        "Development Status :: Production/Alpha",
        "License :: GPL",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Topic :: Internet :: Leaderboard"
        )
    )