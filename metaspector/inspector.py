# metaspector/inspector.py
# !/usr/bin/env python3

import os
import logging
import struct
from typing import Dict, Optional, Any, BinaryIO

from .format_handlers.mp4.mp4 import Mp4Parser
from .format_handlers.flac.flac import FlacParser
from .format_handlers.mp3.mp3 import Mp3Parser

logger = logging.getLogger(__name__)


class MediaInspector:
    def __init__(self, filepath: str):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found at '{filepath}'")
        self.filepath = filepath

    def _get_parser_instance(self, f: BinaryIO):
        """Internal helper to detect file type and return the correct parser instance."""
        initial_check_bytes = f.read(1024)
        f.seek(0)

        if initial_check_bytes.startswith(b"ID3"):
            return Mp3Parser()
        elif initial_check_bytes[0] == 0xFF and (initial_check_bytes[1] & 0xE0) == 0xE0:
            return Mp3Parser()
        elif initial_check_bytes[0:4] == b"fLaC":
            return FlacParser()

        # Robust MP4 check by searching for key atoms
        f.seek(0)
        pos = 0
        while pos < 1024:  # Search within the first 1KB
            f.seek(pos)
            size_bytes = f.read(4)
            if len(size_bytes) < 4:
                break
            size = struct.unpack(">I", size_bytes)[0]

            atom_type = f.read(4)
            if atom_type in (b"ftyp", b"moov", b"mdat"):
                f.seek(0)
                return Mp4Parser()

            if size == 0:
                break  # Cannot determine next position
            pos += size

        f.seek(0)
        return None

    def inspect(self, section: Optional[str] = None) -> Dict[str, Any]:
        """
        Inspects the media file and returns its metadata, audio, video, and subtitle tracks.
        """
        try:
            with open(self.filepath, "rb") as f:
                parser_instance = self._get_parser_instance(f)

                if parser_instance:
                    logger.info(f"Using parser: {type(parser_instance).__name__}")
                    result = parser_instance.parse(f)
                else:
                    raise ValueError(f"Unsupported file format for '{self.filepath}'.")

        except FileNotFoundError:
            raise
        except Exception as e:
            raise IOError(f"Error parsing media file '{self.filepath}': {e}") from e

        if section:
            if section in result:
                return {section: result[section]}
            else:
                raise ValueError(
                    f"Invalid section '{section}'. Available sections are: {', '.join(result.keys())}"
                )
        return result

    def get_cover_art(self) -> Optional[bytes]:
        """
        Extracts and returns the raw cover art bytes from the media file.
        """
        try:
            with open(self.filepath, "rb") as f:
                parser_instance = self._get_parser_instance(f)
                if parser_instance and hasattr(parser_instance, "get_cover_art"):
                    return parser_instance.get_cover_art(f)
                return None
        except Exception as e:
            logger.error(f"Error getting cover art: {e}")
            return None