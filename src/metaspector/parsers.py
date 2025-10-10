# metaspector/parsers.py
# !/usr/bin/env python3

"""
This module provides the main parser class(es) for media formats.
It acts as a central import point for format-specific parsers.
"""

from src.metaspector.format_handlers.mp4.mp4 import Mp4Parser
from src.metaspector.format_handlers.mp3.mp3 import Mp3Parser
from src.metaspector.format_handlers.flac.flac import FlacParser

__all__ = [
    "Mp4Parser",
    "Mp3Parser",
    "FlacParser",
]
