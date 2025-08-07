# metaspector/format_handlers/mp3/mp3_utils.py
# !/usr/bin/env python3

import struct
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

MPEG_VERSIONS = {0b11: "MPEG-1", 0b10: "MPEG-2", 0b00: "MPEG-2.5"}

LAYER_DESCRIPTIONS = {0b11: "Layer I", 0b10: "Layer II", 0b01: "Layer III"}

BITRATE_TABLES = {
    "MPEG-1_Layer-I": {
        1: 32,
        2: 64,
        3: 96,
        4: 128,
        5: 160,
        6: 192,
        7: 224,
        8: 256,
        9: 288,
        10: 320,
        11: 352,
        12: 384,
        13: 416,
        14: 448,
    },
    "MPEG-1_Layer-II": {
        1: 32,
        2: 48,
        3: 56,
        4: 64,
        5: 80,
        6: 96,
        7: 112,
        8: 128,
        9: 160,
        10: 192,
        11: 224,
        12: 256,
        13: 320,
        14: 384,
    },
    "MPEG-1_Layer-III": {
        1: 32,
        2: 40,
        3: 48,
        4: 56,
        5: 64,
        6: 80,
        7: 96,
        8: 112,
        9: 128,
        10: 160,
        11: 192,
        12: 224,
        13: 256,
        14: 320,
    },
    "MPEG-2_Layer-I": {
        1: 32,
        2: 48,
        3: 56,
        4: 64,
        5: 80,
        6: 96,
        7: 112,
        8: 128,
        9: 144,
        10: 160,
        11: 176,
        12: 192,
        13: 224,
        14: 256,
    },
    "MPEG-2_Layer-II": {
        1: 8,
        2: 16,
        3: 24,
        4: 32,
        5: 40,
        6: 48,
        7: 56,
        8: 64,
        9: 80,
        10: 96,
        11: 112,
        12: 128,
        13: 144,
        14: 160,
    },
    "MPEG-2_Layer-III": {
        1: 8,
        2: 16,
        3: 24,
        4: 32,
        5: 40,
        6: 48,
        7: 56,
        8: 64,
        9: 80,
        10: 96,
        11: 112,
        12: 128,
        13: 144,
        14: 160,
    },
    "MPEG-2.5_Layer-I": {
        1: 32,
        2: 48,
        3: 56,
        4: 64,
        5: 80,
        6: 96,
        7: 112,
        8: 128,
        9: 144,
        10: 160,
        11: 176,
        12: 192,
        13: 224,
        14: 256,
    },
    "MPEG-2.5_Layer-II": {
        1: 8,
        2: 16,
        3: 24,
        4: 32,
        5: 40,
        6: 48,
        7: 56,
        8: 64,
        9: 80,
        10: 96,
        11: 112,
        12: 128,
        13: 144,
        14: 160,
    },
    "MPEG-2.5_Layer-III": {
        1: 8,
        2: 16,
        3: 24,
        4: 32,
        5: 40,
        6: 48,
        7: 56,
        8: 64,
        9: 80,
        10: 96,
        11: 112,
        12: 128,
        13: 144,
        14: 160,
    },
}

SAMPLE_RATE_TABLES = {
    "MPEG-1": {0b00: 44100, 0b01: 48000, 0b10: 32000},
    "MPEG-2": {0b00: 22050, 0b01: 24000, 0b10: 16000},
    "MPEG-2.5": {0b00: 11025, 0b01: 12000, 0b10: 8000},
}

CHANNEL_MODES = {
    0b00: "Stereo",
    0b01: "Joint Stereo",
    0b10: "Dual Channel",
    0b11: "Mono",
}

SAMPLES_PER_FRAME = {
    "MPEG-1_Layer-I": 384,
    "MPEG-1_Layer-II": 1152,
    "MPEG-1_Layer-III": 1152,
    "MPEG-2_Layer-I": 384,
    "MPEG-2_Layer-II": 1152,
    "MPEG-2_Layer-III": 576,
    "MPEG-2.5_Layer-I": 384,
    "MPEG-2.5_Layer-II": 1152,
    "MPEG-2.5_Layer-III": 576,
}

ID3_KEY_MAP = {
    "TIT2": "title",
    "TPE1": "artist",
    "TALB": "album",
    "TCOM": "composer",
    "TCON": "genre",
    "TDRC": "release_date",
    "TYER": "release_date",
    "TRCK": "track_number",
    "TPOS": "disc_number",
    "TPE2": "album_artist",
    "USLT": "lyrics",
    "TENC": "encoder",
    "COMM": "comment",
    "TCOP": "copyright",
    "TPUB": "publisher",
    "TSOP": "performer",
    "TMPO": "tempo",
    "TSRC": "isrc",
    "UFID": "unique_file_identifier",
    "TSSE": "encoder",
    "TXXX:REPLAYGAIN_TRACK_GAIN": "replaygain_track_gain",
    "TXXX:REPLAYGAIN_TRACK_PEAK": "replaygain_track_peak",
    "TXXX:REPLAYGAIN_ALBUM_GAIN": "replaygain_album_gain",
    "TXXX:REPLAYGAIN_ALBUM_PEAK": "replaygain_album_peak",
    "TXXX:CUSTOM_TRACKTOTAL": "track_total",
    "TXXX:CUSTOM_DISCTOTAL": "disc_total",
    "TXXX:CUSTOM_LENGTH": "duration_seconds",
    "TXXX:CUSTOM_BPM": "tempo",
    "TXXX:CUSTOM_ISRC": "isrc",
    "TXXX:CUSTOM_BARCODE": "barcode",
    "TXXX:CUSTOM_ITUNESADVISORY": "itunesadvisory",
    "TXXX:ORGANIZATION": "record_company",
    "TXXX:UPC": "upc",
    "TXXX:MEDIA": "media_type",
    "TXXX:DESCRIPTION": "description",
    "TXXX:COMMENT": "comment",
    "TXXX:DATE": "release_date",
    "TXXX:PERFORMER": "performer",
    "TLEN": "duration_seconds",
}


def decode_id3_string(data: bytes, encoding_byte: int) -> str:
    """
    Decodes an ID3v2 string based on the specified encoding byte.
    """
    try:
        if encoding_byte == 0x00:
            decoded_string = data.decode("latin-1", errors="replace")
        elif encoding_byte == 0x01:
            decoded_string = data.decode("utf-16", errors="replace")
        elif encoding_byte == 0x02:
            decoded_string = data.decode("utf-16-be", errors="replace")
        elif encoding_byte == 0x03:
            decoded_string = data.decode("utf-8", errors="replace")
        else:
            logger.warning(
                f"Unknown ID3v2 string encoding: {encoding_byte}. Attempting UTF-8."
            )
            decoded_string = data.decode("utf-8", errors="replace")
    except UnicodeDecodeError:
        logger.error(
            f"Failed to decode string with encoding {encoding_byte}. Falling back to latin-1."
        )
        decoded_string = data.decode("latin-1", errors="replace")
    except Exception as e:
        logger.error(
            f"Error during string decoding (encoding {encoding_byte}): {e}. Data: {data!r}"
        )
        return ""
    return decoded_string.replace("\x00", "").strip()


def parse_image_and_update_metadata(
    image_data: bytes, mime_type: str
) -> Dict[str, Any]:
    """
    Parses image data to get dimensions and returns a metadata dictionary.
    """
    metadata = {
        "has_cover_art": True,
        "cover_art_mime": mime_type,
        "cover_art_dimensions": None,
    }

    width, height = None, None
    if mime_type == "image/jpeg":
        sof_markers = [b"\xff\xc0", b"\xff\xc1", b"\xff\xc2"]
        for marker in sof_markers:
            sof_marker_pos = image_data.find(marker)
            if sof_marker_pos != -1 and len(image_data) >= sof_marker_pos + 9:
                try:
                    height = struct.unpack(
                        ">H", image_data[sof_marker_pos + 5 : sof_marker_pos + 7]
                    )[0]
                    width = struct.unpack(
                        ">H", image_data[sof_marker_pos + 7 : sof_marker_pos + 9]
                    )[0]
                    break
                except Exception:
                    pass
    elif mime_type == "image/png":
        if len(image_data) >= 24 and image_data.startswith(b"\x89PNG\r\n\x1a\n"):
            try:
                width = struct.unpack(">I", image_data[16:20])[0]
                height = struct.unpack(">I", image_data[20:24])[0]
            except Exception:
                pass

    if width is not None and height is not None:
        metadata["cover_art_dimensions"] = f"{width}x{height}"

    return metadata
