# metaspector/inspector.py
# !/usr/bin/env python3

import os
import logging
from typing import Dict, Optional, Any, List

from .format_handlers.mp4.mp4 import Mp4Parser
from .format_handlers.flac.flac import FlacParser
from .format_handlers.mp3.mp3 import Mp3Parser

logger = logging.getLogger(__name__)


class MediaInspector:
    def __init__(self, filepath: str):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found at '{filepath}'")
        self.filepath = filepath

    def inspect(self, section: Optional[str] = None) -> Dict[str, Any]:
        """
        Inspects the media file and returns its metadata, audio, video, and subtitle tracks.
        Optionally, returns only a specific section if 'section' is provided.

        Args:
            section (Optional[str]): The specific section to return ('metadata', 'audio', 'video', 'subtitle').
                                     If None, returns the entire parsed dictionary.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed media information,
                            or a specific section of it.

        Raises:
            ValueError: If an unsupported file format is detected or an invalid section is requested.
            IOError: If an error occurs during file parsing.
        """
        result: Dict[str, Any] = {
            "metadata": {},
            "video": [],
            "audio": [],
            "subtitle": [],
        }

        try:
            with open(self.filepath, "rb") as f:
                initial_check_bytes = f.read(1024)
                f.seek(0)

                if initial_check_bytes.startswith(b"ID3"):
                    logger.debug("Detected ID3 prefix. Assigning Mp3Parser.")
                    parser_instance = Mp3Parser()
                elif (
                    initial_check_bytes[0] == 0xFF
                    and (initial_check_bytes[1] & 0xE0) == 0xE0
                ):
                    logger.debug(
                        "Detected MPEG sync word (no ID3 prefix). Assigning Mp3Parser."
                    )
                    parser_instance = Mp3Parser()
                elif len(initial_check_bytes) >= 8 and (
                    initial_check_bytes[4:8] == b"ftyp"
                    or initial_check_bytes[4:8] == b"moov"
                ):
                    logger.debug("Detected MP4 signature. Assigning Mp4Parser.")
                    parser_instance = Mp4Parser()
                elif initial_check_bytes[0:4] == b"fLaC":
                    logger.debug("Detected FLAC signature. Assigning FlacParser.")
                    parser_instance = FlacParser()
                else:
                    # No known format detected by signature.
                    logger.debug("No known media format signature detected.")
                    parser_instance = None

                # --- Execute the chosen parser and merge results ---
                if parser_instance:
                    logger.info(f"Using parser: {type(parser_instance).__name__}")
                    media_content_parse_result = parser_instance.parse(f)

                    result["metadata"].update(
                        media_content_parse_result.get("metadata", {})
                    )
                    result["video"].extend(media_content_parse_result.get("video", []))
                    result["audio"].extend(media_content_parse_result.get("audio", []))
                    result["subtitle"].extend(
                        media_content_parse_result.get("subtitle", [])
                    )
                else:
                    # If no specific parser was identified for the file.
                    raise ValueError(
                        f"Unsupported file format for '{self.filepath}'. "
                        f"No known media format detected. Initial bytes read: {initial_check_bytes[:20].hex()}..."
                    )

        except FileNotFoundError:
            raise
        except Exception as e:
            raise IOError(f"Error parsing media file '{self.filepath}': {e}") from e

        # --- Conditional output based on 'section' argument ---
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
                initial_check_bytes = f.read(1024)
                f.seek(0)

                if initial_check_bytes.startswith(b"ID3"):
                    parser_instance = Mp3Parser()
                elif (
                    initial_check_bytes[0] == 0xFF
                    and (initial_check_bytes[1] & 0xE0) == 0xE0
                ):
                    parser_instance = Mp3Parser()
                elif len(initial_check_bytes) >= 8 and (
                    initial_check_bytes[4:8] == b"ftyp"
                    or initial_check_bytes[4:8] == b"moov"
                ):
                    parser_instance = Mp4Parser()
                elif initial_check_bytes[:4] == b"fLaC":
                    parser_instance = FlacParser()
                else:
                    return None

                if hasattr(parser_instance, "get_cover_art"):
                    return parser_instance.get_cover_art(f)
                else:
                    return None
        except Exception as e:
            logger.error(f"Error getting cover art: {e}")
            return None
