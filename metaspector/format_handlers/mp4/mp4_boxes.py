# metaspector/format_handlers/mp4/mp4_boxes.py
# !/usr/bin/env python3

import logging
import plistlib
import struct
import io

from typing import Any, BinaryIO, Dict, Optional, Union, Tuple
from .mp4_bitstream_parser import BitstreamParser
from .mp4_utils import (
    _decode_qt_language_code,
    _read_box_header,
    _read_uint8,
    _read_uint16,
    _read_uint32,
    _read_uint64,
)

logger = logging.getLogger(__name__)


class MP4BoxParser:
    """
    A collection of static methods for parsing specific MP4 boxes.
    These methods are designed to be called by Mp4Parser.
    """

    # A mapping of iTunes data format indicators for cover art to MIME types
    _cover_art_format_map = {13: "image/jpeg", 14: "image/png"}

    class _TrackCharacteristics:
        """Holds boolean flags for track characteristics from 'udta'."""

        def __init__(self):
            self.main_program_content = False
            self.auxiliary_content = False
            self.original_content = False
            self.describes_video_for_accessibility = False
            self.enhances_speech_intelligibility = False
            self.dubbed_translation = False
            self.voice_over_translation = False
            self.language_translation = False
            self.forced_only = False
            self.describes_music_and_sound = False
            self.transcribes_spoken_dialog = False
            self.easy_to_read = False

        def update_from_tagc_value(self, text_value: str):
            t = text_value.lower().strip()
            if t == "public.main-program-content":
                self.main_program_content = True
            elif t == "public.auxiliary-content":
                self.auxiliary_content = True
            elif t == "public.original-content":
                self.original_content = True
            elif t == "public.accessibility.describes-video":
                self.describes_video_for_accessibility = True
            elif t == "public.accessibility.enhances-speech-intelligibility":
                self.enhances_speech_intelligibility = True
            elif t == "public.translation.dubbed":
                self.dubbed_translation = True
            elif t == "public.translation.voice-over":
                self.voice_over_translation = True
            elif t == "public.translation":
                self.language_translation = True
            elif t == "public.subtitles.forced-only":
                self.forced_only = True
            elif t == "public.accessibility.describes-music-and-sound":
                self.describes_music_and_sound = True
            elif t == "public.accessibility.transcribes-spoken-dialog":
                self.transcribes_spoken_dialog = True
            elif t == "public.easy-to-read":
                self.easy_to_read = True

    @staticmethod
    def parse_tkhd(f: BinaryIO, box_end: int) -> Optional[int]:
        """Parses 'tkhd' box to get track_id."""
        version = _read_uint8(f)
        f.read(3)
        if version == 1:
            f.read(16)
            track_id = _read_uint32(f)
        elif version == 0:
            f.read(8)
            track_id = _read_uint32(f)
        else:
            track_id = None
        f.seek(box_end)
        return track_id

    @staticmethod
    def parse_mvhd(f: BinaryIO, box_end: int) -> Dict[str, Any]:
        """Parses 'mvhd' box to get the overall movie duration and timescale."""
        details = {"timescale": None, "duration": None}
        version = _read_uint8(f)
        f.read(3)
        if version == 1:
            f.read(16)
            details["timescale"] = _read_uint32(f)
            details["duration"] = _read_uint64(f)
        elif version == 0:
            f.read(8)
            details["timescale"] = _read_uint32(f)
            details["duration"] = _read_uint32(f)

        f.seek(box_end)
        return details

    @staticmethod
    def parse_mdhd(f: BinaryIO, box_end: int) -> Dict[str, Any]:
        """Parses 'mdhd' box to get timescale, duration, and language code."""
        details = {"timescale": None, "duration": None, "lang": "und"}
        version = _read_uint8(f)
        f.read(3)
        if version == 1:
            f.read(16)
            details["timescale"] = _read_uint32(f)
            details["duration"] = _read_uint64(f)
        elif version == 0:
            f.read(8)
            details["timescale"] = _read_uint32(f)
            details["duration"] = _read_uint32(f)
        else:
            f.seek(box_end)
            return details

        lang_and_quality = _read_uint16(f)
        if lang_and_quality is not None:
            details["lang"] = _decode_qt_language_code(lang_and_quality & 0x7FFF)
        f.seek(box_end)
        return details

    @staticmethod
    def parse_hdlr(f: BinaryIO, box_end: int) -> Dict[str, Any]:
        """Parses 'hdlr' box to get handler_type and handler_name."""
        f.read(8)
        handler_type = f.read(4)
        f.read(12)
        name_data = f.read(box_end - f.tell())
        handler_name = (
            name_data.decode("utf-8", errors="replace").rstrip("\x00").strip()
        )
        f.seek(box_end)
        return {"type": handler_type, "name": handler_name}

    @staticmethod
    def parse_elng(f: BinaryIO, box_end: int) -> Optional[str]:
        """Parses 'elng' box for extended language tag."""
        f.seek(4, 1)
        raw_data = f.read(box_end - f.tell())
        text = raw_data.decode("utf-8", errors="replace").split("\x00", 1)[0].strip()
        return text if text else None

    @staticmethod
    def parse_udta(
        f: BinaryIO, udta_end: int
    ) -> tuple["_TrackCharacteristics", Optional[str]]:
        """
        Parses 'udta' box for 'tagc' boxes (track characteristics) and
        a descriptive track name ('©nam', 'name', 'titl').
        Returns a tuple containing the characteristics flags and the track name if found.
        """
        flags = MP4BoxParser._TrackCharacteristics()
        name: Optional[str] = None
        current_pos = f.tell()

        while current_pos < udta_end:
            f.seek(current_pos)
            box_type, _, box_start, box_end = _read_box_header(f)
            if not box_type or box_end > udta_end:
                break

            if box_type == b"tagc":
                tagc_str = (
                    f.read(box_end - f.tell()).decode("utf-8", errors="replace").strip()
                )
                flags.update_from_tagc_value(tagc_str)
            elif box_type in (b"\xa9nam", b"name", b"titl") and name is None:
                f.seek(box_start + 8)
                potential_name = MP4BoxParser.parse_qtss(f, box_end)
                if potential_name:
                    name = potential_name

            current_pos = box_end

        f.seek(udta_end)
        return flags, name

    @staticmethod
    def parse_qtss(f: BinaryIO, box_end: int) -> Optional[str]:
        """Parses a QuickTime-style string metadata atom."""
        current_pos = f.tell()
        if box_end - current_pos >= 4:
            peek_byte = f.read(1)
            f.seek(current_pos)
            if peek_byte == b"\x00":
                f.read(4)
                current_pos = f.tell()

        string_data_length = box_end - current_pos
        if string_data_length <= 0:
            return None

        raw_string_data = f.read(string_data_length)
        decoded_string = (
            raw_string_data.decode("utf-8", errors="replace")
            .split("\x00", 1)[0]
            .strip()
        )
        return decoded_string if decoded_string else None

    @staticmethod
    def parse_itunes_data(
        f: BinaryIO, box_end: int, item_type: bytes
    ) -> Union[str, int, None]:
        """
        Parses the 'data' atom within an iTunes-style metadata item ('ilst').
        It uses the item_type to correctly distinguish between simple integers
        and composite "X of Y" numbers (track_number, disc_number).
        """
        data_start = f.tell()
        if box_end - data_start < 8:
            f.seek(box_end)
            return None

        value_format_indicator = _read_uint32(f)
        f.read(4)  # Skip 4 bytes of unknown purpose

        data_length = box_end - f.tell()
        if data_length < 0:
            f.seek(box_end)
            return None

        raw_data = f.read(data_length)
        f.seek(box_end)

        if not raw_data:
            return None

        try:
            if value_format_indicator == 1:  # UTF-8 String
                return raw_data.decode("utf-8", "replace").strip("\x00").strip()

            if item_type in (b"trkn", b"disk"):
                if len(raw_data) >= 4 and len(raw_data) <= 8:
                    current_num = (
                        int.from_bytes(raw_data[2:4], "big")
                        if len(raw_data) >= 4
                        else None
                    )
                    total_num = (
                        int.from_bytes(raw_data[4:6], "big")
                        if len(raw_data) >= 6
                        else None
                    )
                    if (
                        current_num is not None
                        and total_num is not None
                        and total_num > 0
                    ):
                        return f"{current_num}/{total_num}"
                    elif current_num is not None:
                        return str(current_num)
                return int.from_bytes(raw_data, "big", signed=True)

            if value_format_indicator in (0, 65, 74, 75, 76):
                return int.from_bytes(raw_data, "big", signed=False)
            elif value_format_indicator in (21, 22, 23, 24):
                return int.from_bytes(raw_data, "big", signed=True)
            else:
                logger.debug(
                    f"Unsupported iTunes data format indicator: {value_format_indicator}"
                )
                return None
        except Exception as e:
            logger.error(
                f"Error decoding iTunes data (type {value_format_indicator}, len {len(raw_data)}): {e}"
            )
            return None

    @staticmethod
    def _get_image_dimensions(
        image_data: bytes, mime_type: str
    ) -> Optional[Tuple[int, int]]:
        """
        Safely extracts image dimensions from raw image data without full decoding.
        Supports JPEG and PNG.
        """
        if not image_data:
            return None

        if mime_type == "image/jpeg":
            # JPEG: Find the Start of Frame marker (0xFFC0, 0xFFC1, 0xFFC2, or 0xFFC3)
            # and read the 16-bit height and width fields.
            try:
                data_stream = io.BytesIO(image_data)
                while True:
                    marker_byte = data_stream.read(1)
                    if not marker_byte:
                        break
                    if marker_byte == b"\xff":
                        marker = data_stream.read(1)
                        if marker in (b"\xc0", b"\xc1", b"\xc2", b"\xc3"):
                            data_stream.read(3)  # Skip length and precision
                            height = struct.unpack(">H", data_stream.read(2))[0]
                            width = struct.unpack(">H", data_stream.read(2))[0]
                            return width, height
                        elif marker == b"\xd9":  # End of Image
                            break
            except (IOError, struct.error) as e:
                logger.debug(f"Failed to parse JPEG dimensions: {e}")
            return None

        elif mime_type == "image/png":
            # PNG: The IHDR chunk contains the width and height at fixed offsets.
            # IHDR is always the first chunk after the 8-byte signature.
            if len(image_data) > 24 and image_data[12:16] == b"IHDR":
                try:
                    width = struct.unpack(">I", image_data[16:20])[0]
                    height = struct.unpack(">I", image_data[20:24])[0]
                    return width, height
                except struct.error as e:
                    logger.debug(f"Failed to parse PNG dimensions: {e}")
            return None

        return None

    @staticmethod
    def parse_ilst(
        f: BinaryIO, ilst_end: int
    ) -> Dict[str, Union[str, int, Dict[str, Any], None]]:
        """
        Parses the 'ilst' (item list) atom, which contains individual metadata items.
        It maps common iTunes metadata keys, processes them, and now parses embedded
        XML plists for rich movie metadata, skipping any truncated entries.
        """
        parsed_data: Dict[str, Union[str, int, Dict[str, Any], None]] = {}
        has_cover_art = False
        current_pos = f.tell()

        key_map = {
            b"\xa9nam": "title",
            b"\xa9ART": "artist",
            b"\xa9alb": "album",
            b"\xa9cmt": "comment",
            b"\xa9day": "release_date",
            b"\xa9gen": "genre",
            b"\xa9too": "encoder",
            b"\xa9wrt": "composer",
            b"trkn": "track_number",
            b"disk": "disc_number",
            b"gnre": "genre_id",
            b"covr": "cover_art",
            b"rtng": "itunesadvisory",
            b"cpil": "compilation",
            b"pgap": "gapless_playback",
            b"shwm": "show_name",
            b"eply": "episode_id",
            b"tvsn": "tv_season",
            b"tves": "tv_episode_number",
            b"tven": "tv_episode_id",
            b"desc": "description",
            b"ldes": "long_description",
            b"sdes": "series_description",
            b"pcst": "podcast",
            b"purl": "podcast_url",
            b"egid": "episode_guid",
            b"keyw": "keywords",
            b"catg": "category",
            b"hdvd": "hd_video",
            b"stik": "media_type",
            b"purd": "purchase_date",
            b"cprt": "copyright",
            b"akID": "apple_store_id",
            b"cnID": "content_id",
            b"geid": "genre_id_2",
            b"plID": "playlist_id",
            b"atID": "artist_id",
            b"alID": "album_id",
            b"cmID": "composer_id",
            b"xid ": "external_id",
            b"soal": "sort_album",
            b"soar": "sort_artist",
            b"soco": "sort_composer",
            b"sonm": "sort_name",
            b"sosn": "sort_show",
            b"sotp": "sort_title",
            b"aART": "album_artist",
            b"\xa9grp": "grouping",
            b"tmpo": "tempo",
            b"tvnn": "tv_network",
            b"stvd": "studio",
            b"cast": "cast",
            b"dirc": "directors",
            b"codr": "codirector",
            b"prod": "producers",
            b"exec": "executive_producer",
            b"swnm": "screenwriters",
            b"\xa9lyr": "lyrics",
            b"\xa9enc": "encoded_by",
            b"apID": "itunes_account",
            b"sfID": "itunes_country",
            b"ardr": "art_director",
            b"arrn": "arranger",
            b"\xa9aut": "lyricist",
            b"ackn": "acknowledgement",
            b"\xa9con": "conductor",
            b"\xa9lin": "linear_notes",
            b"\xa9mak": "record_company",
            b"\xa9ope": "original_artist",
            b"\xa9phg": "phonogram_rights",
            b"\xa9prd": "song_producer",
            b"perf": "performer",
            b"\xa9pub": "publisher",
            b"seng": "sound_engineer",
            b"solo": "soloist",
            b"crdt": "credits",
            b"\xa9wrk": "work_name",
            b"\xa9mvn": "movement_name",
            b"\xa9mvi": "movement_number",
            b"\xa9mvc": "movement_count",
            b"shwv": "show_work_and_movement",
            b"soaa": "sort_album_artist",
            b"tvsh": "tv_show_name",
            b"----": "content_rating",
            b"ownr": "owner",
        }

        while current_pos < ilst_end:
            f.seek(current_pos)
            item_type, _, item_start, item_end = _read_box_header(f)
            if not item_type or item_end > ilst_end:
                break

            key_name = key_map.get(
                item_type, item_type.decode("ascii", errors="replace").strip()
            )

            item_child_pos = item_start + 8
            while item_child_pos < item_end:
                f.seek(item_child_pos)
                data_type, _, data_start, data_end = _read_box_header(f)
                if not data_type or data_end > item_end:
                    break

                if data_type == b"data":
                    data_pos_before_read = f.tell()
                    value_format_indicator = _read_uint32(f)
                    f.read(4)

                    data_length = data_end - f.tell()
                    raw_data = f.read(data_length)

                    if item_type == b"covr":
                        if value_format_indicator in MP4BoxParser._cover_art_format_map:
                            has_cover_art = True
                            parsed_data["cover_art_mime"] = (
                                MP4BoxParser._cover_art_format_map.get(
                                    value_format_indicator
                                )
                            )
                            dimensions = MP4BoxParser._get_image_dimensions(
                                raw_data, parsed_data["cover_art_mime"]
                            )
                            if dimensions:
                                parsed_data["cover_art_dimensions"] = (
                                    f"{dimensions[0]}x{dimensions[1]}"
                                )
                        else:
                            has_cover_art = True
                            parsed_data["cover_art_mime"] = "application/octet-stream"
                        f.seek(data_end)
                        break

                    f.seek(data_pos_before_read)
                    parsed_value = MP4BoxParser.parse_itunes_data(
                        f, data_end, item_type
                    )

                    if parsed_value is not None:
                        if isinstance(
                            parsed_value, str
                        ) and parsed_value.strip().startswith("<?xml"):
                            try:
                                plist_data = plistlib.loads(
                                    parsed_value.encode("utf-8")
                                )
                                for plist_key, plist_value in plist_data.items():
                                    if plist_key in (
                                        "cast",
                                        "directors",
                                        "producers",
                                        "screenwriters",
                                    ) and isinstance(plist_value, list):
                                        simplified_list = [
                                            item.get("name")
                                            for item in plist_value
                                            if isinstance(item, dict)
                                            and item.get("name")
                                            and not item["name"].endswith("...")
                                        ]
                                        if simplified_list:
                                            parsed_data[plist_key] = simplified_list
                                    else:
                                        parsed_data[plist_key] = plist_value
                            except Exception as e:
                                logger.warning(
                                    f"Failed to parse XML plist data for '{key_name}': {e}"
                                )
                                parsed_data[key_name] = parsed_value
                        elif (
                            key_name in ("track_number", "disc_number")
                            and isinstance(parsed_value, str)
                            and "/" in parsed_value
                        ):
                            try:
                                num, total = map(int, parsed_value.split("/", 1))
                                parsed_data[key_name] = num
                                parsed_data[key_name.replace("_number", "_total")] = (
                                    str(total)
                                )
                            except (ValueError, TypeError):
                                parsed_data[key_name] = parsed_value
                        elif key_name == "hd_video" and isinstance(parsed_value, int):
                            parsed_data[key_name] = bool(parsed_value)
                            hd_map = {3: "2160p UHD", 2: "1080p FHD", 1: "720p HD"}
                            parsed_data["hd_video_definition"] = hd_map.get(
                                parsed_value, "SD"
                            )
                        elif key_name == "content_rating" and isinstance(
                            parsed_value, str
                        ):
                            parts = parsed_value.split("|")
                            if len(parts) >= 3:
                                parsed_data["rating_system"] = (
                                    parts[0] if parts[0] else None
                                )
                                parsed_data["rating_label"] = (
                                    parts[1] if parts[1] else None
                                )
                                try:
                                    rating_unit = int(parts[2])
                                    parsed_data["rating_unit"] = rating_unit
                                    flag_map = {
                                        400: "1080p FHD",
                                        300: "720p HD",
                                        200: "SD",
                                    }
                                    if rating_unit in flag_map:
                                        parsed_data["hd_video_definition"] = flag_map[
                                            rating_unit
                                        ]
                                except (ValueError, IndexError):
                                    parsed_data["rating_unit"] = None
                            else:
                                parsed_data[key_name] = parsed_value
                        elif key_name == "itunesadvisory" and isinstance(
                            parsed_value, int
                        ):
                            if parsed_value in (0, 2):
                                parsed_data[key_name] = "0"
                            elif parsed_value in (1, 4):
                                parsed_data[key_name] = "1"
                            else:
                                parsed_data[key_name] = str(parsed_value)
                        elif key_name in (
                            "compilation",
                            "gapless_playback",
                            "podcast",
                        ) and isinstance(parsed_value, int):
                            parsed_data[key_name] = bool(parsed_value)
                        else:
                            parsed_data[key_name] = parsed_value
                    break
                item_child_pos = data_end
            current_pos = item_end

        if has_cover_art:
            parsed_data["has_cover_art"] = True

        metadata = {}
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
            "length",
            "tempo",
            "publisher",
            "record_company",
            "copyright",
            "isrc",
            "barcode",
            "upc",
            "media_type",
            "itunesadvisory",
            "lyrics",
            "comment",
            "grouping",
            "keywords",
            "description",
            "long_description",
            "series_description",
            "has_cover_art",
            "cover_art_mime",
            "cover_art_dimensions",
            "encoder",
            "encoded_by",
            "language",
            "compilation",
            "gapless_playback",
            "podcast",
            "category",
            "tv_show_name",
            "tv_episode_id",
            "tv_season",
            "tv_episode_number",
            "tv_network",
            "hd_video",
            "hd_video_definition",
            "studio",
            "rating_system",
            "rating_label",
            "rating_unit",
            "content_id",
            "composer",
            "performer",
            "directors",
            "producers",
            "screenwriters",
            "cast",
            "owner",
        ]

        for key in output_order:
            if key in parsed_data:
                metadata[key] = parsed_data.pop(key)

        metadata.update(parsed_data)

        if "media_type" in metadata and metadata["media_type"] == 1:
            metadata.pop("hd_video", None)
            metadata.pop("hd_video_definition", None)
            if "itunesadvisory" not in metadata:
                metadata["itunesadvisory"] = 0
            metadata.pop("content_rating", None)

        f.seek(ilst_end)
        return metadata

    @staticmethod
    def parse_meta(
        f: BinaryIO, meta_end: int
    ) -> Dict[str, Union[str, int, Dict[str, Any], None]]:
        """
        Parses a 'meta' box for general file-level metadata.
        This box often contains an 'ilst' box for iTunes-style metadata.
        """
        metadata: Dict[str, Union[str, int, Dict[str, Any], None]] = {}
        meta_start = f.tell()
        if meta_end - meta_start < 4:
            f.seek(meta_end)
            return metadata

        f.read(4)
        current_pos = f.tell()

        hdlr_parsed = False
        if current_pos < meta_end:
            f.seek(current_pos)
            hdlr_type, hdlr_size, _, hdlr_end = _read_box_header(f)
            if hdlr_type == b"hdlr":
                MP4BoxParser.parse_hdlr(f, hdlr_end)
                hdlr_parsed = True
                current_pos = hdlr_end
            else:
                current_pos += hdlr_size if hdlr_size > 0 else 8

        if not hdlr_parsed:
            logger.warning("No 'hdlr' box found as first child of 'meta'.")

        while current_pos < meta_end:
            f.seek(current_pos)
            box_type, _, _, box_end = _read_box_header(f)
            if not box_type or box_end > meta_end:
                break
            if box_type == b"ilst":
                ilst_metadata = MP4BoxParser.parse_ilst(f, box_end)
                metadata.update(ilst_metadata)
            current_pos = box_end
        f.seek(meta_end)
        return metadata

    @staticmethod
    def parse_stsd_subtitle(f: BinaryIO, stsd_end: int) -> Optional[str]:
        """Parses 'stsd' for subtitle track details."""
        initial_pos = f.tell()
        try:
            f.seek(initial_pos + 8)
            if f.tell() >= stsd_end:
                return None

            entry_type, _, entry_start, entry_end = _read_box_header(f)
            if not entry_type or entry_end > stsd_end:
                return None

            if entry_type in (b"tx3g", b"mp4s", b"subp", b"clcp", b"text"):
                f.seek(entry_start + 8)
                current_child_pos = f.tell()
                while current_child_pos < entry_end:
                    if entry_end - current_child_pos < 8:
                        break
                    f.seek(current_child_pos)
                    child_type, _, child_start, child_end = _read_box_header(f)
                    if not child_type or child_end > entry_end:
                        break

                    if child_type in (
                        b"\xa9nam",
                        b"name",
                        b"titl",
                        b"desc",
                        b"drmi",
                        b"text",
                        b"kind",
                        b"uri ",
                    ):
                        f.seek(child_start + 8)
                        potential_name = MP4BoxParser.parse_qtss(f, child_end)
                        if potential_name:
                            return potential_name
                    current_child_pos = child_end
            return None
        finally:
            f.seek(initial_pos)

    @staticmethod
    def parse_stsd_audio(f: BinaryIO, stsd_end: int) -> Dict[str, Any]:
        """Parses 'stsd' for audio track details."""
        audio_details = {"codec": "unknown", "channels": 0, "sample_rate": 0}
        channel_layout = None
        initial_pos = f.tell()
        f.seek(8, 1)
        if f.tell() >= stsd_end:
            return audio_details

        entry_type, _, entry_start, entry_end = _read_box_header(f)
        if not entry_type:
            return audio_details

        audio_details["codec"] = entry_type.decode("ascii", errors="replace")
        f.seek(entry_start + 8)
        f.read(16)
        audio_details["channels"] = _read_uint16(f)
        audio_details["bits_per_sample"] = _read_uint16(f)
        f.read(4)
        sr = _read_uint32(f)
        if sr:
            audio_details["sample_rate"] = sr >> 16

        current_pos = f.tell()
        while current_pos < entry_end:
            f.seek(current_pos)
            child_type, _, _, child_end = _read_box_header(f)
            if not child_type or child_end > entry_end:
                break

            if child_type == b"dac3":
                f.seek(1, 1)
                bits = _read_uint8(f)
                if bits is not None:
                    acmod = (bits >> 5) & 0x07
                    lfeon = (bits >> 4) & 0x01
                    ac3_channels_map = {0: 2, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 5, 7: 5}
                    main_channels = ac3_channels_map.get(acmod, 0)
                    audio_details["channels"] = main_channels + lfeon
                    layouts = {
                        0: "1+1",
                        1: f"1.{lfeon}",
                        2: f"2.{lfeon}",
                        3: f"3.{lfeon}",
                        4: f"4.{lfeon}",
                    }
                    channel_layout = layouts.get(acmod, f"5.{lfeon}")
                break

            elif child_type == b"dec3":
                if audio_details.get("channels") == 8:
                    channel_layout = "7.1"
                    break
                f.read(2)
                if child_end - f.tell() >= 3:
                    f.seek(1, 1)
                    bits = _read_uint8(f)
                    if bits is not None:
                        acmod = (bits >> 1) & 0x07
                        lfeon = bits & 0x01
                        acmod_to_main_channels = {
                            0: 2,
                            1: 1,
                            2: 2,
                            3: 3,
                            4: 3,
                            5: 4,
                            6: 4,
                            7: 5,
                        }
                        main_channels = acmod_to_main_channels.get(acmod, 0)
                        audio_details["channels"] = main_channels + lfeon
                        if acmod == 0:
                            channel_layout = "1+1"
                        else:
                            channel_layout = f"{main_channels}.{lfeon}"
                break

            current_pos = child_end

        if channel_layout:
            audio_details["channel_layout"] = channel_layout

        f.seek(stsd_end)
        return audio_details

    @staticmethod
    def parse_stsd_video(
        f: BinaryIO,
        stsd_end: int,
        sample_data: Optional[bytes] = None,
        moov_start: Optional[int] = None,
        moov_end: Optional[int] = None,
        track_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Parses 'stsd' for video track details including resolution and HDR format."""
        TRANSFER_CHARACTERISTICS_MAP = {
            1: "BT.709",
            4: "BT.470M",
            5: "BT.470BG",
            6: "BT.601",
            16: "SMPTE ST 2084 (PQ)",
            18: "ARIB STD-B67 (HLG)",
            14: "SMPTE ST 428-1",
        }
        COLOR_PRIMARIES_MAP = {
            1: "BT.709",
            5: "BT.601",
            9: "BT.2020",
            10: "SMPTE ST 2065-1",
            11: "SMPTE ST 428-1",
            12: "SMPTE RP 431-2",
            13: "SMPTE EG 432-1",
        }
        MATRIX_COEFFICIENTS_MAP = {
            0: "RGB",
            1: "BT.709",
            5: "BT.470BG",
            6: "BT.601",
            9: "BT.2020 non-constant",
            10: "BT.2020 constant",
            14: "SMPTE ST 2065-1",
            15: "SMPTE ST 428-1",
        }

        video_details = {
            "codec": "unknown",
            "width": 0,
            "height": 0,
            "hdr_format": "SDR",
            "color_primaries": "Unknown",
            "transfer_characteristics": "Unknown",
            "matrix_coefficients": "Unknown",
            "color_space": "Unknown",
            "color_transfer": "Unknown",
            "color_range": "Unknown",
            "dolby_vision_profile": None,
            "dolby_vision_level": None,
            "dolby_vision": False,
            "dolby_vision_sdr_compatible": False,
        }

        initial_pos = f.tell()
        f.seek(8, 1)
        if f.tell() >= stsd_end:
            f.seek(initial_pos)
            return video_details

        entry_type, _, entry_start, entry_end = _read_box_header(f)
        if not entry_type:
            f.seek(initial_pos)
            return video_details

        video_details["codec"] = entry_type.decode("ascii", errors="replace")
        f.seek(entry_start + 8)
        f.read(24)
        width = _read_uint16(f)
        height = _read_uint16(f)
        if width:
            video_details["width"] = width
        if height:
            video_details["height"] = height

        current_pos = entry_start + 8 + 78
        has_hdr10_container_metadata = False
        container_colr_found = False

        while current_pos < entry_end:
            f.seek(current_pos)
            child_type, _, child_start, child_end = _read_box_header(f)
            if not child_type or child_end > entry_end:
                break

            if child_type in (b"dvcC", b"dvvC"):
                video_details["dolby_vision"] = True
                f.seek(child_start + 10)
                profile_level_word = _read_uint16(f)
                if profile_level_word is not None:
                    video_details["dolby_vision_profile"] = (
                        profile_level_word >> 9
                    ) & 0x7F
                    video_details["dolby_vision_level"] = (
                        profile_level_word >> 3
                    ) & 0x3F

            elif child_type == b"colr":
                container_colr_found = True
                f.seek(child_start + 8)
                parameter_type = f.read(4)
                primaries = _read_uint16(f)
                transfer = _read_uint16(f)
                matrix = _read_uint16(f)

                video_details["color_primaries"] = COLOR_PRIMARIES_MAP.get(
                    primaries, str(primaries)
                )
                video_details["transfer_characteristics"] = (
                    TRANSFER_CHARACTERISTICS_MAP.get(transfer, str(transfer))
                )
                video_details["matrix_coefficients"] = MATRIX_COEFFICIENTS_MAP.get(
                    matrix, str(matrix)
                )

                if parameter_type == b"nclx":
                    range_byte = _read_uint8(f)
                    if range_byte is not None:
                        is_full_range = (range_byte >> 7) & 1
                        video_details["color_range"] = (
                            "Full" if is_full_range else "Limited"
                        )
                else:
                    video_details["color_range"] = "Limited"

            elif child_type == b"mdcv":
                has_hdr10_container_metadata = True

            elif child_type == b"clli":
                pass

            current_pos = child_end

        if not container_colr_found:
            if video_details["codec"] in (
                "hvc1",
                "hev1",
                "dvh1",
                "dvhe",
                "avc1",
                "av01",
            ):
                data_to_parse = None
                if sample_data:
                    data_to_parse = sample_data
                elif (
                    moov_start is not None
                    and moov_end is not None
                    and track_id is not None
                ):
                    original_file_pos = f.tell()
                    extracted_sample = BitstreamParser.extract_sample_data(
                        f, moov_start, moov_end, track_id
                    )
                    f.seek(original_file_pos)
                    if extracted_sample:
                        data_to_parse = extracted_sample

                if data_to_parse:
                    bitstream_details = BitstreamParser.parse_video_bitstream(
                        data_to_parse
                    )

                    keys_from_bitstream = (
                        "color_primaries",
                        "transfer_characteristics",
                        "matrix_coefficients",
                        "color_range",
                    )
                    for key in keys_from_bitstream:
                        if bitstream_details.get(key) not in (None, "Unknown"):
                            video_details[key] = bitstream_details[key]

                    if bitstream_details.get("dolby_vision_profile") is not None:
                        video_details["dolby_vision"] = True
                        video_details["dolby_vision_profile"] = bitstream_details[
                            "dolby_vision_profile"
                        ]
                        video_details["dolby_vision_level"] = bitstream_details[
                            "dolby_vision_level"
                        ]

        if video_details["dolby_vision"]:
            dv_profile = video_details.get("dolby_vision_profile")
            sdr_compatible_profiles = {0, 2, 8, 9, 10}
            if dv_profile in sdr_compatible_profiles:
                if dv_profile == 8 and "hvc" in video_details.get("codec", ""):
                    video_details["dolby_vision_sdr_compatible"] = True
                elif dv_profile == 10 and "av01" in video_details.get("codec", ""):
                    video_details["dolby_vision_sdr_compatible"] = True
                elif dv_profile not in (8, 10):
                    video_details["dolby_vision_sdr_compatible"] = True

            if video_details["color_primaries"] == "Unknown":
                video_details["color_primaries"] = "BT.2020"
            if video_details["transfer_characteristics"] == "Unknown":
                video_details["transfer_characteristics"] = "SMPTE ST 2084 (PQ)"
            if video_details["matrix_coefficients"] == "Unknown":
                video_details["matrix_coefficients"] = "BT.2020 non-constant"

            is_hdr10_base = (
                video_details["transfer_characteristics"] == "SMPTE ST 2084 (PQ)"
                and has_hdr10_container_metadata
            )
            video_details["hdr_format"] = (
                "HDR10, Dolby Vision" if is_hdr10_base else "Dolby Vision"
            )

        elif video_details["transfer_characteristics"] == "ARIB STD-B67 (HLG)":
            video_details["hdr_format"] = "HLG"
        elif (
            video_details["transfer_characteristics"] == "SMPTE ST 2084 (PQ)"
            and has_hdr10_container_metadata
        ):
            video_details["hdr_format"] = "HDR10"
        elif video_details["transfer_characteristics"] == "SMPTE ST 2084 (PQ)":
            video_details["hdr_format"] = "HDR (PQ)"

        if video_details.get("matrix_coefficients") != "Unknown":
            video_details["color_space"] = video_details["matrix_coefficients"]
        if video_details.get("transfer_characteristics") != "Unknown":
            video_details["color_transfer"] = video_details["transfer_characteristics"]

        if video_details.get("color_range") == "Unknown":
            video_details["color_range"] = "Limited"

        if not video_details.get("dolby_vision"):
            video_details.pop("dolby_vision", None)
            video_details.pop("dolby_vision_profile", None)
            video_details.pop("dolby_vision_level", None)
            video_details.pop("dolby_vision_sdr_compatible", None)

        if video_details.get("hdr_format") == "SDR":
            video_details.pop("color_primaries", None)
            video_details.pop("matrix_coefficients", None)
            video_details.pop("transfer_characteristics", None)

        f.seek(stsd_end)
        return video_details
