# coding=utf-8

from emft.__version__ import __version__
from emft.core import nice_exit


def version():
    print(__version__)
    nice_exit(0)
