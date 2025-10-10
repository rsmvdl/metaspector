#!/usr/bin/env python3

import logging
import struct
import io
from urllib import request
from urllib.error import URLError, HTTPError
from typing import Dict, Optional, Any
import os

from .format_handlers.mp4.mp4 import Mp4Parser
from .format_handlers.flac.flac import FlacParser
from .format_handlers.mp3.mp3 import Mp3Parser

logger = logging.getLogger(__name__)


class MediaInspector:
    def __init__(self, source_path: str):
        self.source_path = source_path
        self.CHUNK_SIZE = 32 * 1024
        self.MP3_AUDIO_BUFFER_SIZE = 128 * 1024
        self.FLAC_METADATA_BUFFER_SIZE = 1 * 1024 * 1024

    def _fetch_range(self, start: int, length: int) -> Optional[bytes]:
        """Fetches a specific length of bytes from a start position."""
        try:
            end = start + length - 1
            headers = {"Range": f"bytes={start}-{end}"}
            req = request.Request(self.source_path, headers=headers)
            with request.urlopen(req, timeout=10) as response:
                if 200 <= response.status < 300:
                    return response.read()
        except (HTTPError, URLError) as e:
            logger.error(f"HTTP error fetching range bytes={start}-{end}: {e}")
            return None
        return None

    def _get_parser_class_from_signature(self, signature: bytes) -> Optional[type]:
        """Identifies the file type from a signature and returns the parser class."""
        if signature.startswith(b"ID3"):
            return Mp3Parser
        if len(signature) > 1 and signature[0] == 0xFF and (signature[1] & 0xE0) == 0xE0:
            return Mp3Parser
        if signature.startswith(b"fLaC"):
            return FlacParser
        if signature.find(b'ftyp') in range(4, 100):
            return Mp4Parser
        return None

    def _handle_remote_mp3(self, operation_func, header_data: bytes):
        """Intelligently fetches the full ID3 tag for remote MP3 files."""
        logger.info("MP3 detected. Fetching full ID3 tag.")
        try:
            size_bytes = header_data[6:10]
            id3_size = (
                    ((size_bytes[0] & 0x7F) << 21)
                    | ((size_bytes[1] & 0x7F) << 14)
                    | ((size_bytes[2] & 0x7F) << 7)
                    | (size_bytes[3] & 0x7F)
            )
            total_tag_size = id3_size + 10
            logger.info(f"ID3 tag size is {total_tag_size} bytes.")

            bytes_to_fetch = total_tag_size + self.MP3_AUDIO_BUFFER_SIZE
            full_data = self._fetch_range(0, bytes_to_fetch)

            if not full_data:
                raise IOError("Failed to fetch full ID3 tag and audio buffer.")

            stream = io.BytesIO(full_data)
            return operation_func(stream, Mp3Parser())
        except (IndexError, struct.error) as e:
            raise IOError(f"Could not parse ID3 header: {e}")

    def _handle_remote_flac(self, operation_func):
        """
        Fetches a large initial chunk for FLAC files to ensure all metadata
        blocks (including cover art) are captured.
        """
        logger.info(f"FLAC detected. Fetching {self.FLAC_METADATA_BUFFER_SIZE} bytes for metadata.")
        full_data = self._fetch_range(0, self.FLAC_METADATA_BUFFER_SIZE)
        if not full_data:
            raise IOError("Failed to fetch FLAC metadata buffer.")

        stream = io.BytesIO(full_data)
        return operation_func(stream, FlacParser())

    def _crawl_remote_mp4(self, operation_func):
        """The specialized dynamic parser for complex MP4s."""
        logger.info("Complex MP4 detected. Activating dynamic crawler.")
        remote_offset = 0
        downloaded_buffer = bytearray()
        ftyp_atom = None
        max_atoms_to_check = 100

        for _ in range(max_atoms_to_check):
            if len(downloaded_buffer) < 16:
                chunk = self._fetch_range(remote_offset, self.CHUNK_SIZE)
                if not chunk: break
                downloaded_buffer.extend(chunk)

            try:
                size = struct.unpack('>I', downloaded_buffer[0:4])[0]
                atom_type = downloaded_buffer[4:8]
                header_size = 8
                if size == 1:
                    size = struct.unpack('>Q', downloaded_buffer[8:16])[0]
                    header_size = 16
                elif size == 0:
                    break
                if size < header_size: break
            except (struct.error, IndexError):
                break

            if atom_type == b'ftyp':
                ftyp_atom = downloaded_buffer[0:size]
                downloaded_buffer = downloaded_buffer[size:]
                remote_offset += size
                continue

            if atom_type == b'moov':
                if len(downloaded_buffer) < size:
                    needed = size - len(downloaded_buffer)
                    extra_data = self._fetch_range(remote_offset + len(downloaded_buffer), needed)
                    if extra_data: downloaded_buffer.extend(extra_data)

                final_data = (ftyp_atom or b'') + downloaded_buffer[0:size]
                return operation_func(io.BytesIO(final_data), Mp4Parser())

            if atom_type == b'mdat':
                remote_offset += size
                downloaded_buffer = bytearray()
                continue

            if len(downloaded_buffer) < size:
                remote_offset += size
                downloaded_buffer = bytearray()
            else:
                downloaded_buffer = downloaded_buffer[size:]
                remote_offset += size

        return operation_func(io.BytesIO(b''), None)

    def _process_source(self, operation_func):
        """Master function to handle both remote and local files."""
        if self.source_path.startswith(("http://", "https://")):
            # For remote files, first fetch a small signature to decide the strategy
            signature_chunk = self._fetch_range(0, 4096)
            if not signature_chunk:
                raise IOError(f"Failed to fetch initial data from '{self.source_path}'")

            parser_class = self._get_parser_class_from_signature(signature_chunk)

            if parser_class == Mp3Parser:
                return self._handle_remote_mp3(operation_func, signature_chunk)
            elif parser_class == FlacParser:
                return self._handle_remote_flac(operation_func)
            elif parser_class == Mp4Parser and b'moov' not in signature_chunk:
                return self._crawl_remote_mp4(operation_func)
            else:
                parser_instance = parser_class() if parser_class else None
                return operation_func(io.BytesIO(signature_chunk), parser_instance)
        else:
            if not os.path.exists(self.source_path):
                raise FileNotFoundError(f"File not found at '{self.source_path}'")
            with open(self.source_path, "rb") as f:
                return operation_func(f, None)

    def inspect(self, section: Optional[str] = None) -> Dict[str, Any]:
        """Inspects a media file and returns its metadata."""

        def _parse_op(f, parser):
            if parser is None:
                signature = f.read(4096)
                f.seek(0)
                parser_class = self._get_parser_class_from_signature(signature)
                if not parser_class:
                    return {"metadata": {"error": "Unsupported file format"}, "video": [], "audio": [], "subtitle": []}
                parser = parser_class()

            return parser.parse(f)

        try:
            result = self._process_source(_parse_op)
            if section:
                return {section: result[section]} if section in result else {}
            return result
        except (IOError, FileNotFoundError, ValueError) as e:
            logger.error(f"An error occurred during inspection: {e}")
            return {"metadata": {"error": str(e)}, "video": [], "audio": [], "subtitle": []}

    def get_cover_art(self) -> Optional[bytes]:
        """Extracts and returns the raw cover art from the media file."""

        def _cover_op(f, parser):
            if parser is None:  # For local files
                signature = f.read(4096)
                f.seek(0)
                parser_class = self._get_parser_class_from_signature(signature)
                if not parser_class: return None
                parser = parser_class()

            if hasattr(parser, 'get_cover_art'):
                return parser.get_cover_art(f)
            return None

        try:
            return self._process_source(_cover_op)
        except (IOError, FileNotFoundError, ValueError) as e:
            logger.error(f"Could not get cover art: {e}")
            return None