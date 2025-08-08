# metaspector/__init__.py
# !/usr/bin/env python3

__version__ = "0.1.3"
__author__ = "RSMVDL"

from .cli import inspect, export
from .inspector import MediaInspector
from ._exceptions import MetaspectorError
