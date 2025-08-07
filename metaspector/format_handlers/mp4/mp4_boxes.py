# metaspector/format_handlers/mp4/mp4_boxes.py
# !/usr/bin/env python3

import logging
import plistlib
import struct
import io

from typing import Any, BinaryIO, Dict, Optional, Union, Tuple
from .mp4_bitstream_parser import BitReader
from .mp4_utils import (
    _decode_qt_language_code,
    _read_box_header,
    _read_uint8,
    _read_uint16,
    _read_uint32,
    _read_uint64,
    TRANSFER_CHARACTERISTICS_MAP,
    COLOR_PRIMARIES_MAP,
    MATRIX_COEFFICIENTS_MAP,
)
from metaspector.matrices.rating_matrix import get_age_classification

logger = logging.getLogger(__name__)


class MP4BoxParser:
    """
    A collection of static methods for parsing specific MP4 boxes.
    These methods are designed to be called by Mp4Parser.
    """

    # A mapping of iTunes data format indicators for cover art to MIME types
    _cover_art_format_map = {13: "image/jpeg", 14: "image/png"}

    # A mapping of video codec FourCC tags to common codec names
    _video_codec_map = {
        "avc1": "h264",
        "avc3": "h264",
        "hvc1": "hevc",
        "hev1": "hevc",
        "dvh1": "hevc",
        "dvhe": "hevc",
        "av01": "av1",
        "vp09": "vp9",
        "mp4v": "mpeg4",
    }

    # A mapping of audio codec FourCC tags to common codec names
    _audio_codec_map = {
        "ec-3": "eac3",
        "ac-3": "ac3",
        "mp4a": "aac",
        "alac": "alac",
        "flac": "flac",
        "dts+": "dts-hd",
        "dtsc": "dts",
        "dtse": "dts-es",
        "dtsh": "dts-hd",
        "dtsl": "dts-hd ma",
        "samr": "amr",
        "sawb": "amr-wb",
    }

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
    def _unescape_nal_payload(payload: bytes) -> bytes:
        """Removes emulation prevention bytes (0x03) from a NAL unit payload."""
        res = bytearray()
        i = 0
        while i < len(payload):
            if i + 2 < len(payload) and payload[i : i + 3] == b"\x00\x00\x03":
                res.extend(b"\x00\x00")
                i += 3
            else:
                res.append(payload[i])
                i += 1
        return bytes(res)

    @staticmethod
    def _parse_avcC_for_pix_fmt(f: BinaryIO, box_end: int) -> Optional[str]:
        """
        Parses an 'avcC' box to determine the pixel format from the first SPS.
        """
        avcc_start = f.tell()
        try:
            f.seek(
                avcc_start + 5
            )  # Skip version, profile, compat, level, lengthSizeMinusOne
            num_sps = _read_uint8(f) & 0x1F
            if num_sps is None or num_sps == 0:
                return None

            sps_len = _read_uint16(f)
            if sps_len is None or sps_len == 0:
                return None

            sps_payload = f.read(sps_len)
            unescaped_sps = MP4BoxParser._unescape_nal_payload(sps_payload)
            reader = BitReader(unescaped_sps)

            profile_idc = reader.read_bits(8)
            reader.read_bits(8)  # constraint_set_flags
            reader.read_bits(8)  # level_idc
            reader.read_ue()  # seq_parameter_set_id

            chroma_format_idc, bit_depth = 1, 8
            if profile_idc in [
                100, 110, 122, 244, 44, 83, 86, 118, 128, 138, 139, 134, 135,
            ]:
                chroma_format_idc = reader.read_ue()
                if chroma_format_idc == 3:
                    reader.read_bit()
                bit_depth = reader.read_ue() + 8

            pix_fmt_map = {0: "gray", 1: "yuv420p", 2: "yuv422p", 3: "yuv444p"}
            pix_fmt_base = pix_fmt_map.get(chroma_format_idc)
            if pix_fmt_base is None:
                return None

            return f"{pix_fmt_base}{bit_depth}le" if bit_depth > 8 else pix_fmt_base
        except (IndexError, struct.error) as e:
            logger.debug(f"Error parsing avcC for pixel format: {e}")
            return None
        finally:
            f.seek(box_end)

    @staticmethod
    def _parse_hvcC_for_pix_fmt(f: BinaryIO, box_end: int) -> Optional[str]:
        """
        Parses an 'hvcC' box to determine the pixel format from the first SPS.
        """
        hvcC_start = f.tell()
        try:
            f.seek(hvcC_start + 22)
            num_of_arrays = _read_uint8(f)
            if num_of_arrays is None:
                return None

            sps_payload = None
            for _ in range(num_of_arrays):
                array_info = _read_uint8(f)
                nal_unit_type = array_info & 0x3F
                num_nalus = _read_uint16(f)
                if num_nalus is None:
                    continue
                for _ in range(num_nalus):
                    nal_unit_len = _read_uint16(f)
                    if nal_unit_len is None:
                        continue
                    if nal_unit_type == 33 and sps_payload is None:
                        sps_payload = f.read(nal_unit_len)
                    else:
                        f.seek(nal_unit_len, 1)

            if sps_payload is None:
                return None

            unescaped_sps = MP4BoxParser._unescape_nal_payload(sps_payload)
            reader = BitReader(unescaped_sps)

            reader.read_bits(16)
            reader.read_bits(4)
            sps_max_sub_layers_minus1 = reader.read_bits(3)
            reader.read_bit()

            reader.read_bits(96)
            sub_layer_profile_present_flag, sub_layer_level_present_flag = [], []
            if sps_max_sub_layers_minus1 > 0:
                for _ in range(sps_max_sub_layers_minus1):
                    sub_layer_profile_present_flag.append(reader.read_bit())
                    sub_layer_level_present_flag.append(reader.read_bit())
                for _ in range(sps_max_sub_layers_minus1, 8):
                    reader.read_bits(2)
            for i in range(sps_max_sub_layers_minus1):
                if sub_layer_profile_present_flag[i]:
                    reader.read_bits(88)
                if sub_layer_level_present_flag[i]:
                    reader.read_bits(8)

            reader.read_ue()
            chroma_format_idc = reader.read_ue()
            if chroma_format_idc == 3:
                reader.read_bit()

            reader.read_ue()
            reader.read_ue()
            if reader.read_bit():
                reader.read_ue()
                reader.read_ue()
                reader.read_ue()
                reader.read_ue()

            bit_depth = reader.read_ue() + 8

            pix_fmt_map = {0: "gray", 1: "yuv420p", 2: "yuv422p", 3: "yuv444p"}
            pix_fmt_base = pix_fmt_map.get(chroma_format_idc)
            if pix_fmt_base is None:
                return None

            return f"{pix_fmt_base}{bit_depth}le" if bit_depth > 8 else pix_fmt_base
        except (IndexError, struct.error) as e:
            logger.debug(f"Error parsing hvcC for pixel format: {e}")
            return None
        finally:
            f.seek(box_end)

    @staticmethod
    def _parse_av1C_for_pix_fmt(f: BinaryIO, box_end: int) -> Optional[str]:
        """Parses an 'av1C' box to determine the pixel format."""
        av1c_start = f.tell()
        try:
            # The needed flags are in the first 4 bytes of the AV1CC record
            if box_end - av1c_start < 4:
                return None

            f.read(2)  # Skip marker, version, seq_profile, seq_level_idx_0
            config_byte = _read_uint8(f)
            if config_byte is None:
                return None

            # Unpack the bit fields from the third byte
            high_bitdepth = (config_byte >> 6) & 0x01
            twelve_bit = (config_byte >> 5) & 0x01
            mono_chrome = (config_byte >> 4) & 0x01
            chroma_subsampling_x = (config_byte >> 3) & 0x01
            chroma_subsampling_y = (config_byte >> 2) & 0x01

            # Determine bit depth
            bit_depth = 8
            if high_bitdepth:
                bit_depth = 12 if twelve_bit else 10

            # Determine chroma format
            if mono_chrome:
                pix_fmt_base = "gray"
            else:
                if chroma_subsampling_x == 1 and chroma_subsampling_y == 1:
                    pix_fmt_base = "yuv420p"
                elif chroma_subsampling_x == 1 and chroma_subsampling_y == 0:
                    pix_fmt_base = "yuv422p"
                elif chroma_subsampling_x == 0 and chroma_subsampling_y == 0:
                    pix_fmt_base = "yuv444p"
                else:  # Should not happen in valid streams
                    return None

            # Construct final string
            if bit_depth > 8:
                return f"{pix_fmt_base}{bit_depth}le"
            else:
                return pix_fmt_base

        except (IndexError, struct.error) as e:
            logger.debug(f"Error parsing av1C for pixel format: {e}")
            return None
        finally:
            f.seek(box_end)

    @staticmethod
    def _parse_vpc_config(f: BinaryIO, box_end: int) -> Dict[str, int]:
        """
        Parses a 'vpcC' box and returns a dictionary of its raw values.
        It does not make a final determination of pixel format.
        """
        config: Dict[str, int] = {}
        vpcc_start = f.tell()
        try:
            if box_end - vpcc_start < 1:
                return config

            profile = _read_uint8(f)
            if profile is None:
                return config
            config["profile"] = profile

            # If box is long enough for explicit color fields, read them.
            if box_end - f.tell() >= 7:
                f.read(1)  # level
                config["bit_depth"] = _read_uint8(f)
                config["chroma_subsampling"] = _read_uint8(f)
                f.read(1)  # videoFullRangeFlag
                config["colour_primaries"] = _read_uint8(f)
                config["transfer_characteristics"] = _read_uint8(f)
                config["matrix_coefficients"] = _read_uint8(f)
            # Fallback for short boxes where color info is inferred
            elif profile in (0, 1):
                config["bit_depth"] = 8
                config["chroma_subsampling"] = 0  # 4:2:0

            return config
        except (IOError, struct.error):
            return config
        finally:
            f.seek(box_end)

    @staticmethod
    def parse_tkhd(f: BinaryIO, box_end: int) -> Optional[int]:
        """Parses 'tkhd' box to get index."""
        version = _read_uint8(f)
        f.read(3)
        if version == 1:
            f.read(16)
            index = _read_uint32(f)
        elif version == 0:
            f.read(8)
            index = _read_uint32(f)
        else:
            index = None
        f.seek(box_end)
        return index

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
                                parsed_data[
                                    "cover_art_dimensions"
                                ] = f"{dimensions[0]}x{dimensions[1]}"
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
                        if (
                            isinstance(parsed_value, str)
                            and parsed_value.strip().startswith("<?xml")
                        ):
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
                                parsed_data[
                                    key_name.replace("_number", "_total")
                                ] = str(total)
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
                                system = parts[0] if parts[0] else None
                                label = parts[1] if parts[1] else None
                                parsed_data["rating_system"] = system
                                parsed_data["rating_label"] = label
                                if system and label:
                                    parsed_data[
                                        "rating_age_classification"
                                    ] = get_age_classification(system, label)

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
            "duration_seconds",
            "tempo",
            "publisher",
            "record_company",
            "copyright",
            "isrc",
            "barcode",
            "upc",
            "media_type",
            "itunesadvisory",
            "rating_system",
            "rating_label",
            "rating_age_classification",
            "rating_unit",
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
    def parse_stsd_subtitle(
        f: BinaryIO, stsd_end: int
    ) -> Tuple[Optional[str], Optional[str]]:
        """Parses 'stsd' for subtitle track details, returning codec and a potential descriptive name."""
        codec: Optional[str] = None
        name: Optional[str] = None

        # The file pointer is at the start of the 'stsd' box content.
        # Skip version (1), flags (3), and number of entries (4).
        f.read(8)
        if f.tell() >= stsd_end:
            f.seek(stsd_end)
            return None, None

        # Now we are at the beginning of the first sample entry.
        entry_type, _, entry_start, entry_end = _read_box_header(f)
        if not entry_type or entry_end > stsd_end:
            f.seek(stsd_end)
            return None, None

        codec = entry_type.decode("ascii", errors="replace")

        # The file pointer 'f' is now at the start of the sample entry's content.
        # Look for a descriptive name inside this sample entry.
        if entry_type in (b"tx3g", b"mp4s", b"subp", b"clcp", b"text"):
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
                        name = potential_name
                        break
                current_child_pos = child_end

        f.seek(stsd_end)
        return codec, name

    @staticmethod
    def parse_stsd_audio(f: BinaryIO, stsd_end: int) -> Dict[str, Any]:
        """Parses 'stsd' for audio track details."""
        audio_details = {
            "codec": "unknown",
            "codec_tag_string": "unknown",
            "channels": 0,
            "sample_rate": 0,
        }
        channel_layout = None
        initial_pos = f.tell()
        f.seek(8, 1)
        if f.tell() >= stsd_end:
            return audio_details

        entry_type, _, entry_start, entry_end = _read_box_header(f)
        if not entry_type:
            return audio_details

        codec_tag = entry_type.decode("ascii", errors="replace")
        audio_details["codec_tag_string"] = codec_tag
        audio_details["codec"] = MP4BoxParser._audio_codec_map.get(codec_tag, codec_tag)

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
            index: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Parses 'stsd' for video track details including resolution and HDR format.
        (Refactored for clarity and robustness).
        """
        # 1. Initialization
        video_details = {
            "codec": "unknown", "codec_tag_string": "unknown", "width": 0, "height": 0,
            "pixel_format": None, "hdr_format": "SDR", "color_primaries": "Unknown",
            "transfer_characteristics": "Unknown", "matrix_coefficients": "Unknown",
            "color_space": "Unknown", "color_transfer": "Unknown", "color_range": "Unknown",
            "dolby_vision_profile": None, "dolby_vision_level": None,
            "dolby_vision": False, "dolby_vision_sdr_compatible": False,
        }

        f.seek(8, 1)
        if f.tell() >= stsd_end:
            return video_details

        entry_type, _, entry_start, entry_end = _read_box_header(f)
        if not entry_type:
            return video_details

        codec_tag = entry_type.decode("ascii", "replace")
        video_details.update({
            "codec_tag_string": codec_tag,
            "codec": MP4BoxParser._video_codec_map.get(codec_tag, codec_tag),
        })

        f.seek(entry_start + 8 + 24)
        width, height = _read_uint16(f), _read_uint16(f)
        if width: video_details["width"] = width
        if height: video_details["height"] = height

        # 2. Data Gathering from Child Boxes
        current_pos = entry_start + 8 + 78
        has_mdcv, container_colr_found = False, False
        vpc_data: Dict[str, int] = {}

        # A map of box types to their respective parser functions
        pixel_format_parsers = {
            b"avcC": MP4BoxParser._parse_avcC_for_pix_fmt,
            b"hvcC": MP4BoxParser._parse_hvcC_for_pix_fmt,
            b"av1C": MP4BoxParser._parse_av1C_for_pix_fmt,
        }

        while current_pos < entry_end:
            f.seek(current_pos)
            child_type, _, child_start, child_end = _read_box_header(f)
            if not child_type or child_end > entry_end:
                break

            if child_type in (b"dvcC", b"dvvC"):
                video_details["dolby_vision"] = True
                f.seek(child_start + 10)
                if (val := _read_uint16(f)) is not None:
                    video_details["dolby_vision_profile"] = (val >> 9) & 0x7F
                    video_details["dolby_vision_level"] = (val >> 3) & 0x3F
            elif child_type in pixel_format_parsers:
                if video_details["pixel_format"] is None:
                    video_details["pixel_format"] = pixel_format_parsers[child_type](f, child_end)
            elif child_type == b"vpcC":
                vpc_data = MP4BoxParser._parse_vpc_config(f, child_end)
            elif child_type == b"colr":
                container_colr_found = True
                f.seek(child_start + 8)
                param_type = f.read(4)
                p, t, m = _read_uint16(f), _read_uint16(f), _read_uint16(f)
                video_details["color_primaries"] = COLOR_PRIMARIES_MAP.get(p, str(p))
                video_details["transfer_characteristics"] = TRANSFER_CHARACTERISTICS_MAP.get(t, str(t))
                video_details["matrix_coefficients"] = MATRIX_COEFFICIENTS_MAP.get(m, str(m))
                if param_type == b"nclx" and (rb := _read_uint8(f)) is not None:
                    video_details["color_range"] = "full" if (rb >> 7) & 1 else "tv"
            elif child_type == b"mdcv":
                has_mdcv = True

            current_pos = child_end

        # 3. Interpretation and Finalization
        # Finalize VP9 pixel format using all gathered info
        if codec_tag == "vp09" and vpc_data:
            bit_depth = vpc_data.get("bit_depth")
            chroma = vpc_data.get("chroma_subsampling")
            if video_details.get("transfer_characteristics") in ("smpte2084",
                                                                 "arib-std-b67") and bit_depth is not None and bit_depth < 10:
                bit_depth = 10  # Correct bit_depth based on more reliable HDR signal from 'colr' box
            if chroma is not None and bit_depth is not None:
                pix_fmt_base = {0: "yuv420p", 1: "yuv422p", 2: "yuv444p"}.get(chroma)
                if pix_fmt_base:
                    video_details["pixel_format"] = f"{pix_fmt_base}{bit_depth}le" if bit_depth > 8 else pix_fmt_base

        # Use vpcC as a fallback for color info if 'colr' box was missing
        if not container_colr_found and vpc_data:
            if (p := vpc_data.get("colour_primaries")) is not None: video_details[
                "color_primaries"] = COLOR_PRIMARIES_MAP.get(p, str(p))
            if (t := vpc_data.get("transfer_characteristics")) is not None: video_details[
                "transfer_characteristics"] = TRANSFER_CHARACTERISTICS_MAP.get(t, str(t))
            if (m := vpc_data.get("matrix_coefficients")) is not None: video_details[
                "matrix_coefficients"] = MATRIX_COEFFICIENTS_MAP.get(m, str(m))

        # Determine HDR Format
        if video_details["dolby_vision"]:
            if video_details["color_primaries"] == "Unknown": video_details["color_primaries"] = "bt2020"
            if video_details["transfer_characteristics"] == "Unknown": video_details[
                "transfer_characteristics"] = "smpte2084"
            if video_details["matrix_coefficients"] == "Unknown": video_details["matrix_coefficients"] = "bt2020nc"
            is_hdr10_base = video_details["transfer_characteristics"] == "smpte2084" and has_mdcv
            video_details["hdr_format"] = "HDR10, Dolby Vision" if is_hdr10_base else "Dolby Vision"
            if video_details.get("dolby_vision_profile") in {8, 10} and codec_tag in {"hvc1", "av01"}:
                video_details["dolby_vision_sdr_compatible"] = True
        elif video_details["transfer_characteristics"] == "arib-std-b67":
            video_details["hdr_format"] = "HLG"
        elif video_details["transfer_characteristics"] == "smpte2084":
            video_details["hdr_format"] = "HDR10" if has_mdcv else "HDR (PQ)"

        # Populate derived fields
        if video_details.get("matrix_coefficients") != "Unknown": video_details["color_space"] = video_details[
            "matrix_coefficients"]
        if video_details.get("transfer_characteristics") != "Unknown": video_details["color_transfer"] = video_details[
            "transfer_characteristics"]
        if video_details.get("color_range") == "Unknown": video_details["color_range"] = "tv"

        # 4. Final Cleanup
        if not video_details.get("dolby_vision"):
            for key in ["dolby_vision", "dolby_vision_profile", "dolby_vision_level", "dolby_vision_sdr_compatible"]:
                video_details.pop(key, None)
        if video_details.get("hdr_format") == "SDR":
            for key in ["color_primaries", "matrix_coefficients", "transfer_characteristics"]:
                video_details.pop(key, None)

        f.seek(stsd_end)
        return video_details
