# metaspector/format_handlers/mp4/mp4_utils.py
# !/usr/bin/env python3

import struct
import logging

from typing import BinaryIO, Optional, Tuple

logger = logging.getLogger(__name__)

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
