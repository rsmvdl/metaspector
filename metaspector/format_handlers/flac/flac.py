# metaspector/format_handlers/flac/flac.py
# !/usr/bin/env python3

import struct
import logging

from typing import BinaryIO, Dict, Any, Optional
from metaspector.format_handlers.base import BaseMediaParser
from .flac_boxes import (
    parse_streaminfo_block,
    parse_vorbis_comment_block,
    parse_picture_block_metadata,
    get_cover_art_data,
)
from .flac_utils import order_audio_track, process_metadata_for_output

logger = logging.getLogger(__name__)


class FlacParser(BaseMediaParser):
    """
    Parses FLAC files to extract audio and metadata.
    Handles standard FLAC metadata blocks using correct block type IDs.
    """

    def __init__(self):
        self.key_map = {
            "title": "title",
            "artist": "artist",
            "album": "album",
            "date": "release_date",
            "genre": "genre",
            "tracknumber": "track_number",
            "discnumber": "disc_number",
            "comment": "comment",
            "composer": "composer",
            "lyrics": "lyrics",
            "performer": "performer",
            "albumartist": "album_artist",
            "description": "description",
            "organization": "record_company",
            "isrc": "isrc",
            "barcode": "barcode",
            "upc": "upc",
            "media": "media_type",
            "encoder": "encoder",
            "language": "language",
            "replaygain_track_gain": "replaygain_track_gain",
            "replaygain_track_peak": "replaygain_track_peak",
            "replaygain_album_gain": "replaygain_album_gain",
            "replaygain_album_peak": "replaygain_album_peak",
            "bpm": "tempo",
            "copyright": "copyright",
            "publisher": "publisher",
            "tracktotal": "track_total",
            "totaltracks": "track_total",
            "disctotal": "disc_total",
            "totaldiscs": "disc_total",
        }

    def parse(self, f: BinaryIO) -> Dict[str, Any]:
        """Parses the FLAC file from the given binary stream."""
        audio_tracks = []
        metadata = {"has_cover_art": False}
        total_metadata_size = 0

        f.seek(0, 2)
        total_file_size = f.tell()
        f.seek(0)

        if f.read(4) != b"fLaC":
            raise ValueError("Not a valid FLAC file: missing 'fLaC' magic bytes.")
        total_metadata_size += 4

        last_block = False
        while not last_block:
            current_pos = f.tell()
            header_bytes = f.read(4)
            if len(header_bytes) < 4:
                break

            header_val = struct.unpack(">I", header_bytes)[0]
            last_block = (header_val & 0x80000000) != 0
            block_type = (header_val >> 24) & 0x7F
            block_size = header_val & 0x00FFFFFF
            data_end_pos = current_pos + 4 + block_size
            total_metadata_size += 4 + block_size

            if block_type == 0:  # STREAMINFO
                parse_streaminfo_block(f, audio_tracks)
            elif block_type == 4:  # VORBIS_COMMENT
                parse_vorbis_comment_block(f, block_size, metadata, self.key_map)
            elif block_type == 6:  # PICTURE
                parse_picture_block_metadata(f, metadata)

            f.seek(data_end_pos)

        if audio_tracks and audio_tracks[0].get("duration_seconds", 0) > 0:
            audio_data_size = (
                total_file_size - total_metadata_size
                if total_file_size > total_metadata_size
                else 0
            )
            if audio_data_size > 0:
                bitrate = (audio_data_size * 8) / audio_tracks[0]["duration_seconds"]
                audio_tracks[0]["bitrate_kbps"] = int(bitrate / 1000)

        return {
            "metadata": process_metadata_for_output(metadata),
            "audio": [order_audio_track(track, i) for i, track in enumerate(audio_tracks)],
            "video": [],
            "subtitle": [],
        }

    def get_cover_art(self, f: BinaryIO) -> Optional[bytes]:
        """
        Efficiently finds and extracts the raw cover art data from a FLAC file
        using a robust, stream-based parsing strategy.
        """
        f.seek(0)
        return get_cover_art_data(f)
