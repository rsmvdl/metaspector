# metaspector/format_handlers/mp4/mp4_utils.py
# !/usr/bin/env python3

import struct
import logging

from typing import BinaryIO, Optional, Tuple

logger = logging.getLogger(__name__)

_COVER_ART_FORMAT_MAP = {
    13: "image/jpeg",
    14: "image/png"
}

TRANSFER_CHARACTERISTICS_MAP = {
    1: "bt709",
    4: "bt470m",
    5: "bt470bg",
    6: "smpte170m",
    16: "smpte2084",
    18: "arib-std-b67",
    14: "smpte428",
}

COLOR_PRIMARIES_MAP = {
    1: "bt709",
    5: "smpte170m",
    9: "bt2020",
    10: "smpte428",
    11: "smpte428",
    12: "smpte431",
    13: "smpte432",
}
MATRIX_COEFFICIENTS_MAP = {
    0: "gbr",
    1: "bt709",
    5: "bt470bg",
    6: "smpte170m",
    9: "bt2020nc",
    10: "bt2020c",
    14: "bt2020nc",
    15: "bt2020nc",
}

_CHROMA_LOCATION_MAP = {
    0: "left",
    1: "center",
    2: "topleft",
    3: "top",
    4: "bottomleft",
    5: "bottom",
}

_AV1_CHROMA_LOCATION_MAP = {
    0: "unspecified",
    1: "topleft",
    2: "left",
}

_VIDEO_CODEC_MAP = {
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

_H264_PROFILE_MAP = {
    66: "Baseline",
    77: "Main",
    88: "Extended",
    100: "High",
    103: "Stereo High",
    110: "High 10",
    122: "High 4:2:2",
    128: "Stereo High",
    134: "MFC High",
    135: "MFC Depth High",
    138: "Multi-view Depth High",
    139: "Enhanced Multi-view Depth High",
    144: "High 4:4:4",
    155: "High 4:4:4 Predictive",
    244: "High 4:4:4 Predictive",
    44: "CAVLC 4:4:4 Intra",
    83: "Scalable Baseline",
    86: "Scalable High",
    118: "Multi-view High",
}

_HEVC_PROFILE_MAP = {
    1: "Main",
    2: "Main 10",
    3: "Main Still Picture",
    4: "Range Extension",
    5: "High Throughput",
    6: "High Throughput 10",
    9: "Main 4:4:4",
    10: "Main 4:4:4 10",
    11: "Main 4:4:4 12",
    12: "Main 4:4:4 16",
    17: "Main 12",
    18: "Main 4:2:2",
    19: "Main 4:2:2 10",
    20: "Main 4:2:2 12",
    21: "Main 4:2:2 16",
    25: "Main 4:4:4 10",
    26: "Main 4:4:4 12",
    33: "Main 10",
}

_AV1_PROFILE_MAP = {
    0: "Main",
    1: "High",
    2: "Professional"
}

_VP9_PROFILE_MAP = {
    0: "Profile 0",
    1: "Profile 1",
    2: "Profile 2",
    3: "Profile 3",
}

_AUDIO_CODEC_MAP = {
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

_SUBTITLE_CODEC_MAP = {
    "tx3g": "mov_text",
    "c608": "eia_608",
    "stpp": "ttml",
    "wvtt": "webvtt",
}


def _read_uint8(f: BinaryIO) -> Optional[int]:
    b = f.read(1)
    if not b:
        return None
    return struct.unpack(">B", b)[0]


def _read_uint16(f: BinaryIO) -> Optional[int]:
    b = f.read(2)
    if len(b) < 2:
        return None
    return struct.unpack(">H", b)[0]


def _read_uint32(f: BinaryIO) -> Optional[int]:
    b = f.read(4)
    if len(b) < 4:
        logger.debug(
            f"DEBUG_READ: _read_uint32: EOF or not enough bytes at {f.tell() - len(b)}. Bytes read: {b!r}"
        )
        return None
    return struct.unpack(">I", b)[0]


def _read_uint64(f: BinaryIO) -> Optional[int]:
    b = f.read(8)
    if len(b) < 8:
        logger.debug(
            f"DEBUG_READ: _read_uint64: EOF or not enough bytes at {f.tell() - len(b)}. Bytes read: {b!r}"
        )
        return None
    return struct.unpack(">Q", b)[0]


def _read_box_header(f: BinaryIO) -> Tuple[Optional[bytes], int, int, int]:
    """
    Reads an MP4 box header and returns (type, size, start_pos, end_pos).
    Handles both 32-bit and 64-bit box sizes.
    """
    box_start = f.tell()
    # logger.debug(f"DEBUG_BOX_HEADER: Attempting to read box header at position {box_start}") # Enable this for very verbose logging

    size_32 = _read_uint32(f)
    if size_32 is None:
        logger.debug(
            f"DEBUG_BOX_HEADER: Failed to read 32-bit size at {box_start}. Returning None."
        )
        return None, 0, 0, 0

    box_type_bytes = f.read(4)
    if len(box_type_bytes) < 4:
        logger.debug(
            f"DEBUG_BOX_HEADER: Failed to read 4-byte box type at {f.tell() - len(box_type_bytes)}. Returning None."
        )
        return None, 0, 0, 0

    if size_32 == 1:  # Extended size (64-bit)
        size_64 = _read_uint64(f)
        if size_64 is None:
            logger.debug(
                f"DEBUG_BOX_HEADER: Failed to read 64-bit size for large box at {f.tell() - len(box_type_bytes) - 8}. Returning None."
            )
            return None, 0, 0, 0
        box_size = size_64
    else:  # 32-bit size
        box_size = size_32

    if box_size == 0:  # Box extends to end of file
        file_size = f.seek(0, 2)
        f.seek(box_start)  # Reset position back to start of box before computing end
        box_end = file_size
        logger.debug(
            f"DEBUG_BOX_HEADER: Found box '{box_type_bytes.decode(errors='replace')}' with size 0 (extends to EOF). End: {box_end}"
        )
    elif box_size < 8:  # Minimum box size is 8 bytes (size + type)
        logger.debug(
            f"DEBUG_BOX_HEADER: Invalid box size {box_size} for box '{box_type_bytes.decode(errors='replace')}' at {box_start}. Returning None."
        )
        return None, 0, 0, 0
    else:
        box_end = box_start + box_size

    return box_type_bytes, box_size, box_start, box_end


def _decode_qt_language_code(lang_bits: int) -> str:
    """Decodes a 15-bit QuickTime language code into a 3-letter string."""
    if not (0 <= lang_bits < 32768):
        return "und"
    chars = [(lang_bits >> 10) & 0x1F, (lang_bits >> 5) & 0x1F, lang_bits & 0x1F]
    return "".join(chr(c + 0x60) for c in chars)
