# metaspector/__init__.py
# !/usr/bin/env python3

__version__ = "0.1.0.post2"
__author__ = "RSMVDL"

from .inspector import MediaInspector


class MetaspectorError(Exception):
    """Base exception for the metaspector library."""

    pass
