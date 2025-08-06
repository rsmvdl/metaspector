# metaspector/format_handlers/mp3/mp3_boxes.py
# !/usr/bin/env python3

import struct
import logging
from typing import BinaryIO, Dict, Any, Callable, Optional

logger = logging.getLogger(__name__)

from .mp3_utils import (
    MPEG_VERSIONS,
    LAYER_DESCRIPTIONS,
    BITRATE_TABLES,
    SAMPLE_RATE_TABLES,
    CHANNEL_MODES,
    SAMPLES_PER_FRAME,
    ID3_KEY_MAP,
    parse_image_and_update_metadata,
    decode_id3_string,
)


def parse_id3v2_tag(f: BinaryIO, apply_metadata_func: Callable) -> Dict[str, Any]:
    """
    Parses the ID3v2 tag at the beginning of the file.
    """
    initial_pos = f.tell()
    header = f.read(10)
    if len(header) < 10 or header[0:3] != b"ID3":
        f.seek(initial_pos)
        return {"size": 0, "has_image": False}

    version_major = header[3]
    flags = header[5]
    size = (
        ((header[6] & 0x7F) << 21)
        | ((header[7] & 0x7F) << 14)
        | ((header[8] & 0x7F) << 7)
        | (header[9] & 0x7F)
    )
    id3_tag_size = 10 + size
    id3_tag_end = initial_pos + id3_tag_size

    if flags & 0x40:
        extended_header_start_pos = f.tell()
        extended_header_size_bytes = f.read(4)
        if len(extended_header_size_bytes) < 4:
            logger.warning("Incomplete extended header size. Skipping ID3 parsing.")
            f.seek(id3_tag_end)
            return {"size": id3_tag_size, "has_image": False}
        extended_header_size = struct.unpack(">I", extended_header_size_bytes)[0]
        if (
            extended_header_size > 4
            and extended_header_start_pos + extended_header_size <= id3_tag_end
        ):
            f.read(extended_header_size - 4)
        else:
            logger.warning(
                f"Malformed extended header size {extended_header_size}. Skipping."
            )
            f.seek(id3_tag_end)
            return {"size": id3_tag_size, "has_image": False}

    has_image = False
    image_mime = None
    image_dimensions = None

    while f.tell() < id3_tag_end:
        frame_header = f.read(10)
        if len(frame_header) < 10:
            logger.warning("Incomplete ID3v2 frame header. Stopping ID3 parsing.")
            break

        frame_id = frame_header[0:4].decode("ascii", errors="ignore").strip("\x00")
        if all(b == 0 for b in frame_header):
            break

        if version_major == 4:
            frame_size = (
                ((frame_header[4] & 0x7F) << 21)
                | ((frame_header[5] & 0x7F) << 14)
                | ((frame_header[6] & 0x7F) << 7)
                | (frame_header[7] & 0x7F)
            )
        else:
            frame_size = struct.unpack(">I", frame_header[4:8])[0]

        remaining_in_tag = id3_tag_end - f.tell()
        if frame_size <= 0 or frame_size > remaining_in_tag:
            logger.warning(
                f"Invalid or truncated ID3v2 frame '{frame_id}' (size {frame_size}, remaining {remaining_in_tag}). Skipping."
            )
            f.seek(id3_tag_end)
            break

        frame_data = f.read(frame_size)
        if len(frame_data) < frame_size:
            logger.warning(
                f"Premature EOF while reading data for frame '{frame_id}'. Expected {frame_size}, read {len(frame_data)}. Stopping ID3 parsing."
            )
            break

        parsed_frame = _parse_id3v2_frame_content(frame_id, frame_data)
        if parsed_frame:
            if frame_id == "APIC" and parsed_frame.get("has_cover_art"):
                has_image = True
                image_mime = parsed_frame.get("cover_art_mime")
                image_dimensions = parsed_frame.get("cover_art_dimensions")
            elif frame_id != "APIC":
                for key, value in parsed_frame.items():
                    apply_metadata_func(key, value)
    f.seek(id3_tag_end)
    return {
        "size": id3_tag_size,
        "has_image": has_image,
        "image_mime": image_mime,
        "image_dimensions": image_dimensions,
    }


def _parse_id3v2_frame_content(frame_id: str, data: bytes) -> Dict[str, Any]:
    """
    Parses the content of a single ID3v2 frame.
    """
    metadata = {}
    if frame_id.startswith("T") and frame_id != "TXXX" and frame_id != "TFLT":
        if not data:
            return {}
        encoding = data[0]
        content = data[1:]
        decoded_content = decode_id3_string(content, encoding)
        normalized_key = ID3_KEY_MAP.get(frame_id, frame_id.lower())
        metadata[normalized_key] = decoded_content
    elif frame_id == "USLT":
        if not data or len(data) < 7:
            return {}
        encoding = data[0]
        language = data[1:4].decode("ascii", errors="ignore").strip("\x00")
        null_term_size = 2 if encoding == 0x01 or encoding == 0x02 else 1
        desc_start_offset = 4
        desc_end_index = -1
        if null_term_size == 2:
            for i in range(
                desc_start_offset, len(data) - null_term_size + 1, null_term_size
            ):
                if data[i : i + null_term_size] == b"\x00" * null_term_size:
                    desc_end_index = i
                    break
        else:
            desc_end_index = data.find(b"\x00", desc_start_offset)
        if desc_end_index == -1:
            text_content = data[desc_start_offset:]
        else:
            text_content = data[desc_end_index + null_term_size :]
        decoded_lyrics = decode_id3_string(text_content, encoding)
        normalized_lyrics = (
            decoded_lyrics.replace("\r\n", "\n").replace("\r", "\n").strip()
        )
        metadata["lyrics"] = normalized_lyrics
        metadata["language"] = language
    elif frame_id == "TXXX":
        if not data:
            return {}
        encoding = data[0]
        content = data[1:]
        null_term_size = 2 if encoding == 0x01 or encoding == 0x02 else 1
        key_end_index = -1
        if null_term_size == 2:
            for i in range(0, len(content) - null_term_size + 1, null_term_size):
                if content[i : i + null_term_size] == b"\x00" * null_term_size:
                    key_end_index = i
                    break
        else:
            key_end_index = content.find(b"\x00")
        if key_end_index == -1:
            logger.warning("TXXX frame: missing key null terminator.")
            return {}
        key_raw = content[:key_end_index]
        value_raw = content[key_end_index + null_term_size :]
        key = decode_id3_string(key_raw, encoding)
        value = decode_id3_string(value_raw, encoding)
        normalized_key = ID3_KEY_MAP.get(f"TXXX:{key.upper()}", key.lower())
        if key.upper() == "CM/REPUBLIC":
            normalized_key = "publisher"
        elif key.upper() == "TSSE":
            normalized_key = "encoder"
        metadata[normalized_key] = value
    elif frame_id == "APIC":
        metadata = {
            "has_cover_art": False,
            "cover_art_mime": None,
            "cover_art_dimensions": None,
        }
        if not data or len(data) < 2:
            return metadata
        offset = 0
        encoding = data[offset]
        offset += 1
        null_term = b"\x00"
        try:
            mime_end = data.index(null_term, offset)
            mime_type = data[offset:mime_end].decode("latin-1", errors="ignore")
            offset = mime_end + 1
        except ValueError:
            return metadata
        if len(data) <= offset:
            return metadata
        offset += 1
        if encoding in [0x01, 0x02]:
            null_term = b"\x00\x00"
        else:
            null_term = b"\x00"
        try:
            desc_end = data.index(null_term, offset)
            offset = desc_end + len(null_term)
        except ValueError:
            pass
        image_data = data[offset:]
        if image_data:
            image_info = parse_image_and_update_metadata(image_data, mime_type)
            metadata.update(image_info)
    elif frame_id == "UFID":
        if not data or b"\x00" not in data:
            return {}
        owner_id_end = data.find(b"\x00", 1)
        if owner_id_end == -1:
            return {}
        owner_id = data[1:owner_id_end].decode("latin-1", errors="replace").strip()
        identifier_data = data[owner_id_end + 1 :]
        if owner_id == "http://www.id3.org/uslt/iTunes":
            try:
                if identifier_data.startswith(b"isrc"):
                    isrc = (
                        identifier_data[4:]
                        .decode("latin-1", errors="replace")
                        .strip("\x00")
                    )
                    metadata["isrc"] = isrc
                elif identifier_data.startswith(b"barcode"):
                    barcode = (
                        identifier_data[7:]
                        .decode("latin-1", errors="replace")
                        .strip("\x00")
                    )
                    metadata["barcode"] = barcode
            except UnicodeDecodeError:
                pass
    return metadata


def search_for_image_data(
    f: BinaryIO, id3_tag_size: int, total_file_size: int
) -> Optional[Dict[str, Any]]:
    """
    Searches for an image embedded in the audio data if not found in the ID3 tag.
    """
    initial_pos = f.tell()
    f.seek(id3_tag_size)
    data_chunk_size = 64 * 1024

    while f.tell() < total_file_size:
        start_pos = f.tell()
        chunk = f.read(data_chunk_size)
        if not chunk:
            break

        jpeg_start = chunk.find(b"\xff\xd8\xff")
        if jpeg_start != -1:
            f.seek(start_pos + jpeg_start)
            image_data = f.read()
            f.seek(initial_pos)
            return parse_image_and_update_metadata(image_data, "image/jpeg")

        png_start = chunk.find(b"\x89PNG\r\n\x1a\n")
        if png_start != -1:
            f.seek(start_pos + png_start)
            image_data = f.read()
            f.seek(initial_pos)
            return parse_image_and_update_metadata(image_data, "image/png")

    f.seek(initial_pos)
    return None


def get_mpeg_audio_properties(
    f: BinaryIO, id3_tag_size: int, total_file_size: int
) -> Optional[Dict[str, Any]]:
    """
    Searches for and parses the first valid MPEG audio frame to get properties.
    """
    original_pos = f.tell()
    f.seek(id3_tag_size)
    initial_audio_data_pos = f.tell()
    buffer_size = 64 * 1024
    frame_length_bytes = None
    first_frame_bitrate = None
    first_frame_sample_rate = None
    first_frame_channels = None
    first_frame_codec = None
    first_frame_samples_per_frame = None

    while True:
        current_read_pos = f.tell()
        data_chunk = f.read(buffer_size)
        if not data_chunk:
            break
        for i in range(len(data_chunk) - 4):
            header_bytes = data_chunk[i : i + 4]
            if header_bytes[0] == 0xFF and (header_bytes[1] & 0xE0) == 0xE0:
                try:
                    header_int = struct.unpack(">I", header_bytes)[0]
                except struct.error:
                    continue
                mpeg_version_bits = (header_int >> 19) & 0x03
                layer_bits = (header_int >> 17) & 0x03
                bitrate_index = (header_int >> 12) & 0x0F
                sample_rate_index = (header_int >> 10) & 0x03
                padding_bit = (header_int >> 9) & 0x01
                channel_mode_bits = (header_int >> 6) & 0x03
                if (
                    mpeg_version_bits == 0b01
                    or layer_bits == 0b00
                    or bitrate_index == 0
                    or bitrate_index == 0x0F
                    or sample_rate_index == 0x03
                ):
                    continue
                mpeg_version = MPEG_VERSIONS.get(mpeg_version_bits)
                layer = LAYER_DESCRIPTIONS.get(layer_bits)
                channels_str = CHANNEL_MODES.get(channel_mode_bits)
                if not mpeg_version or not layer or channels_str is None:
                    continue
                bitrate_map_key = f"{mpeg_version}_{layer.replace(' ', '-')}"
                bitrate_kbps_from_frame = BITRATE_TABLES.get(bitrate_map_key, {}).get(
                    bitrate_index
                )
                sample_rate = SAMPLE_RATE_TABLES.get(mpeg_version, {}).get(
                    sample_rate_index
                )
                if bitrate_kbps_from_frame is None or sample_rate is None:
                    continue
                channels = 1 if channels_str == "Mono" else 2
                sps_key = f"{mpeg_version}_{layer.replace(' ', '-')}"
                samples_per_frame = SAMPLES_PER_FRAME.get(sps_key)
                if not samples_per_frame:
                    continue
                if layer_bits == 0b11:
                    frame_length_bytes = (
                        int(
                            ((12 * bitrate_kbps_from_frame * 1000.0) / sample_rate)
                            + padding_bit
                        )
                        * 4
                    )
                else:
                    frame_length_bytes = int(
                        ((144 * bitrate_kbps_from_frame * 1000.0) / sample_rate)
                        + padding_bit
                    )
                if frame_length_bytes <= 0:
                    continue
                check_pos = current_read_pos + i + frame_length_bytes
                if check_pos + 4 <= total_file_size:
                    f.seek(check_pos)
                    next_header_peek = f.read(4)
                    f.seek(current_read_pos + i)
                    if (
                        len(next_header_peek) == 4
                        and next_header_peek[0] == 0xFF
                        and (next_header_peek[1] & 0xE0) == 0xE0
                    ):
                        first_frame_bitrate = bitrate_kbps_from_frame
                        first_frame_sample_rate = sample_rate
                        first_frame_channels = channels
                        first_frame_codec = f"MPEG Audio {layer}"
                        first_frame_samples_per_frame = samples_per_frame
                        initial_audio_data_pos = current_read_pos + i
                        break
        if first_frame_bitrate is not None:
            break
        f.seek(current_read_pos + len(data_chunk) - 4)
        if f.tell() >= total_file_size:
            break
    f.seek(original_pos)
    if first_frame_bitrate is None:
        return None
    total_samples = 0
    if (
        first_frame_sample_rate > 0
        and first_frame_bitrate > 0
        and total_file_size > initial_audio_data_pos
    ):
        estimated_audio_bytes = total_file_size - initial_audio_data_pos
        if frame_length_bytes > 0:
            estimated_total_frames = estimated_audio_bytes / frame_length_bytes
            total_samples = int(estimated_total_frames * first_frame_samples_per_frame)
    return {
        "codec": first_frame_codec,
        "channels": first_frame_channels,
        "sample_rate": first_frame_sample_rate,
        "bits_per_sample": 16,
        "duration_seconds": None,
        "total_samples": total_samples,
        "initial_frame_bitrate_kbps": first_frame_bitrate,
    }


def get_apic_frame_data(f: BinaryIO) -> Optional[bytes]:
    """
    Specifically searches for an APIC frame in an ID3v2 tag and extracts the raw image data.
    This function is self-contained and safe to call for cover art extraction.
    """
    f.seek(0)
    header = f.read(10)
    if len(header) < 10 or header[0:3] != b"ID3":
        return None

    version_major = header[3]
    size = (
        ((header[6] & 0x7F) << 21)
        | ((header[7] & 0x7F) << 14)
        | ((header[8] & 0x7F) << 7)
        | (header[9] & 0x7F)
    )
    id3_tag_end = 10 + size

    # Skip extended header if present
    if header[5] & 0x40:
        f.seek(10)
        ext_header_size_bytes = f.read(4)
        if len(ext_header_size_bytes) < 4:
            return None
        ext_header_size = struct.unpack(">I", ext_header_size_bytes)[0]
        if ext_header_size > 4:
            f.read(ext_header_size - 4)

    while f.tell() < id3_tag_end:
        frame_header = f.read(10)
        if len(frame_header) < 10 or all(b == 0 for b in frame_header):
            break

        frame_id = frame_header[0:4].decode("ascii", errors="ignore")

        if version_major == 4:
            frame_size = (
                ((frame_header[4] & 0x7F) << 21)
                | ((frame_header[5] & 0x7F) << 14)
                | ((frame_header[6] & 0x7F) << 7)
                | (frame_header[7] & 0x7F)
            )
        else:
            frame_size = struct.unpack(">I", frame_header[4:8])[0]

        current_pos = f.tell()
        if frame_size <= 0 or current_pos + frame_size > id3_tag_end:
            break

        if frame_id == "APIC":
            frame_data = f.read(frame_size)
            try:
                encoding_byte = frame_data[0]
                offset = 1  # Start after encoding byte

                # Skip over MIME type string
                mime_end = frame_data.index(b"\x00", offset)
                offset = mime_end + 1

                # Skip picture type byte
                offset += 1

                # Skip over description string
                null_term = b"\x00\x00" if encoding_byte in [1, 2] else b"\x00"
                desc_end = frame_data.index(null_term, offset)
                offset = desc_end + len(null_term)

                # The rest of the frame is the image data
                return frame_data[offset:]
            except (ValueError, IndexError):
                # Malformed APIC frame, continue searching
                f.seek(current_pos + frame_size)
                continue
        else:
            f.seek(frame_size, 1)

    return None
