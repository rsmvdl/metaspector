# metaspector/format_handlers/mp3/mp3.py
# !/usr/bin/env python3

import logging
from typing import BinaryIO, Dict, List, Any, Optional

from .mp3_boxes import (
    parse_id3v2_tag,
    search_for_image_data,
    get_mpeg_audio_properties,
    get_apic_frame_data,
)
from ..base import BaseMediaParser

logger = logging.getLogger(__name__)


class Mp3Parser(BaseMediaParser):
    def __init__(self):
        self.metadata: Dict[str, Any] = {}
        self.audio_tracks: List[Dict[str, Any]] = []
        self.total_file_size: int = 0
        self.id3_tag_size: int = 0

    def parse(self, f: BinaryIO) -> Dict[str, Any]:
        self.metadata = {
            "has_cover_art": None,
            "cover_art_mime": None,
            "cover_art_dimensions": None,
        }
        self.audio_tracks = []
        f.seek(0, 2)
        self.total_file_size = f.tell()
        f.seek(0)

        id3_tag_data = parse_id3v2_tag(f, self._apply_metadata_field)
        self.id3_tag_size = id3_tag_data.get("size", 0)
        if id3_tag_data.get("has_image"):
            self.metadata["has_cover_art"] = True
            self.metadata["cover_art_mime"] = id3_tag_data.get("image_mime")
            self.metadata["cover_art_dimensions"] = id3_tag_data.get("image_dimensions")

        if not self.metadata.get("has_cover_art"):
            image_data = search_for_image_data(
                f, self.id3_tag_size, self.total_file_size
            )
            if image_data:
                self.metadata.update(image_data)

        audio_info = get_mpeg_audio_properties(
            f, self.id3_tag_size, self.total_file_size
        )
        if audio_info:
            if "length" in self.metadata and self.metadata["length"] is not None:
                try:
                    duration_from_tag = int(self.metadata["length"]) / 1000.0
                    audio_info["duration_seconds"] = duration_from_tag
                except (ValueError, TypeError):
                    logger.warning(
                        f"Could not convert ID3 TLEN '{self.metadata['length']}' to seconds. Falling back to calculated duration."
                    )
                    audio_info["duration_seconds"] = None

            if (
                audio_info.get("duration_seconds") is None
                and audio_info.get("total_samples") is not None
                and audio_info.get("sample_rate") is not None
                and audio_info["sample_rate"] > 0
            ):
                audio_info["duration_seconds"] = (
                    audio_info["total_samples"] / audio_info["sample_rate"]
                )

            if (
                audio_info.get("duration_seconds") is not None
                and audio_info["duration_seconds"] > 0
            ):
                audio_data_size_bytes = self.total_file_size - self.id3_tag_size
                if audio_data_size_bytes > 0:
                    average_bitrate_bps = (audio_data_size_bytes * 8) / audio_info[
                        "duration_seconds"
                    ]
                    audio_info["bitrate_kbps"] = round(average_bitrate_bps / 1000)
                else:
                    audio_info["bitrate_kbps"] = None

            if (
                audio_info.get("bitrate_kbps") is None
                and audio_info.get("initial_frame_bitrate_kbps") is not None
            ):
                audio_info["bitrate_kbps"] = audio_info["initial_frame_bitrate_kbps"]

            self.audio_tracks.append(
                {
                    "track_id": 1,
                    "handler_name": "Audio",
                    "language": self.metadata.get("language", "und"),
                    **{
                        k: v
                        for k, v in audio_info.items()
                        if k not in ["initial_frame_bitrate_kbps"]
                    },
                }
            )

        final_audio_tracks = []
        for track in self.audio_tracks:
            ordered_track = self._order_audio_track(track)
            final_audio_tracks.append(ordered_track)

        final_metadata = self._process_metadata_for_output(self.metadata)

        return {
            "metadata": final_metadata,
            "audio": final_audio_tracks,
            "video": [],
            "subtitle": [],
        }

    def get_cover_art(self, f: BinaryIO) -> Optional[bytes]:
        """
        Extracts the raw cover art from the MP3 file's ID3v2 tag by finding
        the APIC frame.
        """
        f.seek(0)
        return get_apic_frame_data(f)

    def _order_audio_track(self, track: Dict[str, Any]) -> Dict[str, Any]:
        """Reorders audio track fields for consistent output."""
        ordered_keys = [
            "track_id",
            "handler_name",
            "language",
            "codec",
            "channels",
            "sample_rate",
            "bits_per_sample",
            "bitrate_kbps",
            "duration_seconds",
            "total_samples",
        ]

        ordered_dict = {}
        for key in ordered_keys:
            if key in track:
                ordered_dict[key] = track.pop(key)

        ordered_dict.update(track)
        return ordered_dict

    def _apply_metadata_field(self, key: str, value: Any):
        if key == "track_number":
            try:
                if isinstance(value, str) and "/" in value:
                    num_str, total_str = value.split("/", 1)
                    self.metadata[key] = int(num_str)
                    self.metadata["track_total"] = str(total_str)
                else:
                    self.metadata[key] = int(value)
            except (ValueError, TypeError):
                self.metadata[key] = value
        elif key == "disc_number":
            try:
                if isinstance(value, str) and "/" in value:
                    num_str, total_str = value.split("/", 1)
                    self.metadata[key] = int(num_str)
                    self.metadata["disc_total"] = str(total_str)
                else:
                    self.metadata[key] = int(value)
            except (ValueError, TypeError):
                self.metadata[key] = value
        elif key == "tempo":
            try:
                self.metadata[key] = int(float(value))
            except (ValueError, TypeError):
                self.metadata[key] = value
        elif key == "release_date":
            if isinstance(value, str):
                if len(value) == 4 and value.isdigit():
                    try:
                        year = int(value)
                        if 1900 < year < 2100:
                            self.metadata[key] = str(year)
                        else:
                            self.metadata[key] = value
                    except ValueError:
                        self.metadata[key] = value
                elif len(value) == 10 and value[4] == "-" and value[7] == "-":
                    self.metadata[key] = value
                else:
                    self.metadata[key] = value
            else:
                self.metadata[key] = value
        elif key in [
            "replaygain_track_gain",
            "replaygain_track_peak",
            "replaygain_album_gain",
            "replaygain_album_peak",
            "lyrics",
            "encoder",
            "comment",
            "copyright",
            "publisher",
            "performer",
            "language",
            "record_company",
            "upc",
            "media_type",
            "description",
            "isrc",
            "barcode",
            "track_total",
            "disc_total",
        ]:
            self.metadata[key] = str(value).strip()
        elif key == "length":
            self.metadata[key] = str(value).strip()
        elif key == "itunesadvisory":
            if isinstance(value, bool):
                self.metadata[key] = "1" if value else "0"
            else:
                self.metadata[key] = str(value).strip()
        else:
            self.metadata[key] = value

    def _process_metadata_for_output(
        self, raw_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        processed_metadata = {}
        output_order = [
            "title",
            "artist",
            "album",
            "album_artist",
            "track_number",
            "track_total",
            "disc_number",
            "disc_total",
            "genre",
            "release_date",
            "publisher",
            "isrc",
            "barcode",
            "upc",
            "media_type",
            "replaygain_track_gain",
            "replaygain_album_gain",
            "lyrics",
            "composer",
            "copyright",
            "has_cover_art",
            "cover_art_mime",
            "cover_art_dimensions",
            "comment",
            "encoder",
            "performer",
            "language",
            "record_company",
            "description",
            "tempo",
            "length",
            "itunesadvisory",
        ]

        temp_data = {}
        for key in list(raw_metadata.keys()):
            temp_data[key] = raw_metadata.pop(key)

        for key_in_order in output_order:
            if key_in_order in temp_data:
                processed_metadata[key_in_order] = temp_data.pop(key_in_order)

        for key, value in temp_data.items():
            if (
                value is not None
                and value != ""
                and key
                not in [
                    "duration_seconds",
                    "bitrate_kbps",
                    "unique_file_identifier",
                    "tlen",
                    "tdat",
                ]
            ):
                processed_metadata[key] = value

        if "track_total" in processed_metadata:
            processed_metadata["track_total"] = str(processed_metadata["track_total"])
        if "disc_total" in processed_metadata:
            processed_metadata["disc_total"] = str(processed_metadata["disc_total"])

        return processed_metadata
