# metaspector/format_handlers/flac/flac_boxes.py
# !/usr/bin/env python3

import struct
import logging
import base64

from typing import BinaryIO, Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def parse_streaminfo_block(f: BinaryIO, audio_tracks: List[Dict]) -> None:
    """Parses the STREAMINFO block for core audio properties."""
    data = f.read(34)
    if len(data) < 34:
        return
    props = struct.unpack(">Q", data[10:18])[0]
    sample_rate = (props >> 44) & 0xFFFFF
    total_samples = props & 0xFFFFFFFFF
    duration = total_samples / sample_rate if sample_rate > 0 else 0.0

    # Determine channels and channel layout
    num_channels = ((props >> 41) & 0x07) + 1
    channel_layout_map = {
        1: "1.0",
        2: "2.0",
        3: "3.0",
        4: "4.0",
        5: "5.0",
        6: "5.1",
        7: "6.1",
        8: "7.1",
    }
    channel_layout = channel_layout_map.get(num_channels)

    audio_tracks.append(
        {
            "codec": "flac",
            "codec_tag_string": "FLAC (Free Lossless Audio Codec)",
            "channels": num_channels,
            "channel_layout": channel_layout,
            "sample_rate": sample_rate,
            "bits_per_sample": ((props >> 36) & 0x1F) + 1,
            "duration_seconds": duration,
            "total_samples": total_samples,
        }
    )


def parse_vorbis_comment_block(
    f: BinaryIO, block_size: int, metadata: Dict, key_map: Dict
) -> None:
    """Parses a VORBIS_COMMENT block for key-value metadata tags."""
    data = f.read(block_size)
    try:
        offset = 4 + struct.unpack("<I", data[0:4])[0]
        if offset > len(data):
            return

        comment_count = struct.unpack("<I", data[offset : offset + 4])[0]
        offset += 4

        for _ in range(comment_count):
            if offset + 4 > len(data):
                break
            length = struct.unpack("<I", data[offset : offset + 4])[0]
            offset += 4
            if offset + length > len(data):
                break

            comment_str = data[offset : offset + length].decode("utf-8", "replace")
            offset += length

            if "=" in comment_str:
                key, value = comment_str.split("=", 1)
                if key.upper() == "METADATA_BLOCK_PICTURE":
                    metadata["has_cover_art"] = True
                else:
                    _apply_metadata_field(metadata, key.lower(), value, key_map)
    except (struct.error, IndexError, ValueError) as e:
        logger.warning(f"Could not parse VORBIS_COMMENT block: {e}")


def parse_picture_block_metadata(f: BinaryIO, metadata: Dict) -> None:
    """Parses a PICTURE block's headers for its descriptive metadata."""
    try:
        f.read(4)
        mime_len = struct.unpack(">I", f.read(4))[0]
        mime_type = f.read(mime_len).decode("ascii", "ignore")
        desc_len = struct.unpack(">I", f.read(4))[0]
        description = f.read(desc_len).decode("utf-8", "replace")
        width, height, _, _, _ = struct.unpack(">5I", f.read(20))

        metadata.update(
            {
                "has_cover_art": True,
                "cover_art_mime": mime_type,
                "cover_art_dimensions": f"{width}x{height}",
            }
        )
        if description:
            metadata["cover_art_description"] = description
    except (struct.error, IOError):
        logger.warning("Could not parse PICTURE block metadata.")


def get_cover_art_data(f: BinaryIO) -> Optional[bytes]:
    """
    Efficiently finds and extracts the raw cover art data from a FLAC file
    using a robust, stream-based parsing strategy.
    """
    if f.read(4) != b"fLaC":
        return None

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

        image_bytes = None
        if block_type == 6:  # PICTURE
            try:
                f.read(4)
                mime_len = struct.unpack(">I", f.read(4))[0]
                f.read(mime_len)
                desc_len = struct.unpack(">I", f.read(4))[0]
                f.read(desc_len)
                f.read(16)
                data_len = struct.unpack(">I", f.read(4))[0]
                image_bytes = f.read(data_len)
            except (struct.error, IOError):
                pass
        elif block_type == 4:  # VORBIS_COMMENT
            data = f.read(block_size)
            try:
                offset = 4 + struct.unpack("<I", data[0:4])[0]
                count = struct.unpack("<I", data[offset : offset + 4])[0]
                offset += 4
                for _ in range(count):
                    if offset + 4 > len(data):
                        break
                    length = struct.unpack("<I", data[offset : offset + 4])[0]
                    offset += 4
                    if offset + length > len(data):
                        break
                    comment = data[offset : offset + length].decode("utf-8")
                    offset += length
                    if comment.upper().startswith("METADATA_BLOCK_PICTURE="):
                        b64_data = comment.split("=", 1)[1]
                        image_bytes = base64.b64decode(b64_data)
                        break
            except (struct.error, IndexError, ValueError, base64.binascii.Error):
                pass

        if image_bytes:
            return image_bytes

        f.seek(data_end_pos)
    return None


def _apply_metadata_field(metadata: dict, key: str, value: Any, key_map: Dict):
    """Maps a raw metadata key to the final output key and sets the value."""
    output_key = key_map.get(key, key)
    if output_key in ["track_number", "disc_number"] and "/" in str(value):
        try:
            num, total = str(value).split("/", 1)
            metadata[output_key] = int(num)
            metadata[output_key.replace("_number", "_total")] = int(total)
        except (ValueError, TypeError):
            metadata[output_key] = value
    elif output_key in [
        "track_number",
        "disc_number",
        "track_total",
        "disc_total",
        "itunesadvisory",
        "barcode",
        "duration_seconds",
        "tempo",
    ]:
        try:
            metadata[output_key] = int(value)
        except (ValueError, TypeError):
            metadata[output_key] = value
    else:
        metadata[output_key] = value
