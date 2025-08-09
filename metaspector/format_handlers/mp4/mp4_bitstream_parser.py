# metaspector/format_handlers/mp4/mp4_bitstream_parser.py
# !/usr/bin/env python3

import logging
import struct

from typing import BinaryIO, Dict, Any, Optional
from .mp4_utils import (
    _read_box_header,
    _read_uint8,
    _read_uint32,
    _read_uint64,
    COLOR_PRIMARIES_MAP,
    TRANSFER_CHARACTERISTICS_MAP,
    MATRIX_COEFFICIENTS_MAP,
)

logger = logging.getLogger(__name__)


class BitReader:
    """A helper class for reading bits from a byte stream."""

    def __init__(self, data: bytes):
        self.data = data
        self.byte_pos = 0
        self.bit_pos = 0

    def read_bit(self) -> int:
        if self.byte_pos >= len(self.data):
            raise IndexError("Reading past end of data")
        byte = self.data[self.byte_pos]
        bit = (byte >> (7 - self.bit_pos)) & 1
        self.bit_pos += 1
        if self.bit_pos == 8:
            self.bit_pos = 0
            self.byte_pos += 1
        return bit

    def read_bits(self, num_bits: int) -> int:
        value = 0
        for _ in range(num_bits):
            value = (value << 1) | self.read_bit()
        return value

    def read_ue(self) -> int:
        leading_zeros = 0
        while self.byte_pos < len(self.data) and self.read_bit() == 0:
            leading_zeros += 1
            if self.byte_pos >= len(self.data) and self.bit_pos == 0:
                break

        if self.byte_pos >= len(self.data) and leading_zeros > 0:
            raise IndexError("Reading past end of data while parsing Exp-Golomb")

        return (1 << leading_zeros) - 1 + self.read_bits(leading_zeros)

    def read_se(self) -> int:
        value = self.read_ue()
        if value & 1:
            return (value + 1) // 2
        else:
            return -1 * (value // 2)

    def byte_aligned(self) -> bool:
        return self.bit_pos == 0

    def skip_to_next_byte(self):
        if self.bit_pos != 0:
            self.bit_pos = 0
            self.byte_pos += 1


class BitstreamParser:
    """
    A collection of static methods for parsing bitstream-level data
    (e.g., video SPS/VUI, SEI messages) and extracting sample data.
    """

    @staticmethod
    def extract_sample_data(
        f: BinaryIO, moov_start: int, moov_end: int, index: int
    ) -> Optional[bytes]:
        """
        Navigates the MP4 structure to find and extract the raw data of the first
        sample for a given index. This is essential for bitstream parsing.
        """
        logger.debug(f"Attempting to extract first sample for track ID: {index}")
        f.seek(moov_start)

        while f.tell() < moov_end:
            box_type, _, box_start, box_end = _read_box_header(f)
            if not box_type:
                break
            if f.tell() > moov_end:
                break

            if box_type == b"trak":
                trak_start = f.tell() - 8

                is_correct_track = False
                f.seek(trak_start)
                while f.tell() < box_end:
                    inner_type, _, _, inner_end = _read_box_header(f)
                    if not inner_type or inner_end > box_end:
                        break
                    if inner_type == b"tkhd":
                        f.read(8)  # version + flags
                        version = _read_uint8(f)
                        f.read(3)  # flags
                        if version == 1:
                            f.read(16)
                            found_id = _read_uint32(f)
                        elif version == 0:
                            f.read(8)
                            found_id = _read_uint32(f)
                        else:
                            found_id = None

                        if found_id == index:
                            is_correct_track = True
                        break
                    f.seek(inner_end)

                if is_correct_track:
                    logger.debug(f"Found correct 'trak' for track ID {index}")
                    f.seek(trak_start)
                    stbl_start, stbl_end = 0, 0
                    current_pos_trak = trak_start
                    while current_pos_trak < box_end:
                        f.seek(current_pos_trak)
                        b_type, _, b_start, b_end = _read_box_header(f)
                        if not b_type or b_end > box_end:
                            break
                        if b_type == b"stbl":
                            stbl_start, stbl_end = b_start, b_end
                            break
                        if b_type in (b"mdia", b"minf"):
                            current_pos_trak = b_start
                        else:
                            current_pos_trak = b_end

                    if not stbl_start:
                        logger.error("Could not find 'stbl' box for the track.")
                        return None

                    first_sample_size = None
                    first_chunk_offset = None
                    f.seek(stbl_start)
                    while f.tell() < stbl_end:
                        stbl_box_type, _, stbl_box_start, stbl_box_end = (
                            _read_box_header(f)
                        )
                        if not stbl_box_type or stbl_box_end > stbl_end:
                            break

                        if stbl_box_type == b"stsz":
                            f.seek(stbl_box_start + 8)
                            sample_size = _read_uint32(f)
                            entry_count = _read_uint32(f)
                            if sample_size == 0 and entry_count > 0:
                                first_sample_size = _read_uint32(f)
                            else:
                                first_sample_size = sample_size
                            logger.debug(
                                f"Found first sample size: {first_sample_size}"
                            )

                        elif stbl_box_type == b"stco":
                            f.seek(stbl_box_start + 8)
                            entry_count = _read_uint32(f)
                            if entry_count > 0:
                                first_chunk_offset = _read_uint32(f)
                            logger.debug(
                                f"Found 32-bit chunk offset: {first_chunk_offset}"
                            )

                        elif stbl_box_type == b"co64":
                            f.seek(stbl_box_start + 8)
                            entry_count = _read_uint32(f)
                            if entry_count > 0:
                                first_chunk_offset = _read_uint64(f)
                            logger.debug(
                                f"Found 64-bit chunk offset: {first_chunk_offset}"
                            )

                        if (
                            first_sample_size is not None
                            and first_chunk_offset is not None
                        ):
                            break

                        f.seek(stbl_box_end)

                    if first_sample_size is not None and first_chunk_offset is not None:
                        try:
                            logger.info(
                                f"Extracting sample of size {first_sample_size} from offset {first_chunk_offset}"
                            )
                            f.seek(first_chunk_offset)
                            return f.read(first_sample_size)
                        except Exception as e:
                            logger.error(f"Failed to seek/read sample data: {e}")
                            return None

            f.seek(box_end)

        logger.warning(
            f"Could not find sample data for track ID {index}. 'trak' may not exist or parsing failed."
        )
        return None

    @staticmethod
    def _parse_vui_parameters(reader: BitReader, details: Dict[str, Any]):
        """Parses VUI parameters from a video bitstream."""
        try:
            if reader.read_bit():  # aspect_ratio_info_present_flag
                aspect_ratio_idc = reader.read_bits(8)
                if aspect_ratio_idc == 255:  # SAR_Extended
                    reader.read_bits(16)  # sar_width
                    reader.read_bits(16)  # sar_height

            if reader.read_bit():  # overscan_info_present_flag
                reader.read_bit()  # overscan_appropriate_flag

            if reader.read_bit():  # video_signal_type_present_flag
                reader.read_bits(3)  # video_format
                details["video_full_range_flag"] = reader.read_bit()
                if reader.read_bit():  # colour_description_present_flag
                    details["color_primaries"] = reader.read_bits(8)
                    details["transfer_characteristics"] = reader.read_bits(8)
                    details["matrix_coefficients"] = reader.read_bits(8)
                    logger.debug(
                        f"VUI: Primaries: {details['color_primaries']}, Transfer: {details['transfer_characteristics']}, Matrix: {details['matrix_coefficients']}, Range: {details.get('video_full_range_flag')}"
                    )

            if reader.read_bit():  # chroma_loc_info_present_flag
                reader.read_ue()  # chroma_sample_loc_type_top_field
                reader.read_ue()  # chroma_sample_loc_type_bottom_field

            if reader.read_bit():  # neutral_chroma_indication_flag
                pass
            if reader.read_bit():  # field_seq_flag
                pass
            if reader.read_bit():  # frame_field_info_present_flag
                pass

            # Simplified parsing for the rest of VUI
        except IndexError:
            logger.warning("Reached end of VUI payload prematurely during parsing.")
        except Exception as e:
            logger.error(f"Error parsing VUI parameters: {e}")

    @staticmethod
    def _parse_sps_payload(nal_payload: bytes, details: Dict[str, Any]):
        """
        Parses a SPS NAL unit payload to extract VUI parameters.
        This is a simplified implementation focusing only on VUI for color info.
        """
        reader = BitReader(nal_payload)

        try:
            reader.read_bits(4)
            reader.read_bits(3)
            reader.read_bit()

            reader.read_bits(2)
            reader.read_bit()
            reader.read_bits(5)

            reader.read_bits(32)
            reader.read_bits(48)

            reader.read_bits(8)

            sps_max_sub_layers_minus1 = details.get("sps_max_sub_layers_minus1", 0)
            for i in range(sps_max_sub_layers_minus1 + 1):
                pass

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

            reader.read_ue()
            reader.read_ue()

            reader.read_ue()

            sps_sub_layer_ordering_info_present_flag = reader.read_bit()
            for i in range(sps_max_sub_layers_minus1 + 1):
                reader.read_ue()
                reader.read_ue()
                reader.read_ue()
                if not sps_sub_layer_ordering_info_present_flag:
                    break

            reader.read_ue()
            reader.read_ue()
            reader.read_ue()
            reader.read_ue()
            reader.read_ue()
            reader.read_ue()

            if reader.read_bit():
                if reader.read_bit():
                    pass

            reader.read_bit()
            reader.read_bit()
            reader.read_bit()
            if reader.read_bit():
                reader.read_bits(4)
                reader.read_bits(4)
                reader.read_ue()
                reader.read_ue()
                reader.read_bit()

            reader.read_ue()

            reader.read_bit()
            if reader.read_bit():
                reader.read_ue()

            reader.read_bit()
            reader.read_bit()

            if reader.read_bit():
                logger.debug("VUI parameters present in SPS.")
                BitstreamParser._parse_vui_parameters(reader, details)

            if reader.read_bit():
                pass

            if not reader.byte_aligned():
                reader.skip_to_next_byte()

        except IndexError:
            logger.warning("Reached end of SPS NAL payload prematurely during parsing.")
        except Exception as e:
            logger.error(f"Error parsing SPS NAL unit: {e}")

    @staticmethod
    def parse_video_bitstream(data: bytes) -> Dict[str, Any]:
        """
        Parses a video bitstream for SPS (VUI) and SEI messages containing HDR metadata.
        """
        bitstream_details = {
            "hdr_format": "SDR",
            "color_primaries": "Unknown",
            "transfer_characteristics": "Unknown",
            "matrix_coefficients": "Unknown",
            "color_space": "Unknown",
            "color_transfer": "Unknown",
            "color_range": "Unknown",
            "max_content_light_level": None,
            "max_frame_average_light_level": None,
            "dolby_vision_profile": None,
            "dolby_vision_level": None,
        }

        pos = 0
        logger.debug(f"Parsing video bitstream from {len(data)} bytes")
        while pos < len(data):
            start_code_pos = -1
            start_code_len = 0

            if pos + 4 <= len(data) and data[pos : pos + 4] == b"\x00\x00\x00\x01":
                start_code_pos = pos
                start_code_len = 4
            elif pos + 3 <= len(data) and data[pos : pos + 3] == b"\x00\x00\x01":
                start_code_pos = pos
                start_code_len = 3

            if start_code_pos == -1:
                pos += 1
                continue

            pos = start_code_pos + start_code_len
            if pos + 2 > len(data):
                break

            nal_unit_type = (data[pos] >> 1) & 0x3F

            next_start_code_pos = len(data)
            temp_pos = pos + 2
            while temp_pos < len(data) - 3:
                if data[temp_pos : temp_pos + 4] == b"\x00\x00\x00\x01":
                    next_start_code_pos = temp_pos
                    break
                elif data[temp_pos : temp_pos + 3] == b"\x00\x00\x01":
                    next_start_code_pos = temp_pos
                    break
                temp_pos += 1

            nal_end = next_start_code_pos
            nal_payload = data[pos + 2 : nal_end]

            logger.debug(
                f"Found NAL unit type {nal_unit_type} at offset {start_code_pos}. Payload size: {len(nal_payload)}"
            )

            if nal_unit_type == 33:
                logger.debug("Parsing SPS NAL unit.")
                BitstreamParser._parse_sps_payload(nal_payload, bitstream_details)

                if isinstance(bitstream_details.get("color_primaries"), int):
                    bitstream_details["color_primaries"] = COLOR_PRIMARIES_MAP.get(
                        bitstream_details["color_primaries"],
                        f"Unknown ({bitstream_details['color_primaries']})",
                    )

                if isinstance(bitstream_details.get("transfer_characteristics"), int):
                    bitstream_details["transfer_characteristics"] = (
                        TRANSFER_CHARACTERISTICS_MAP.get(
                            bitstream_details["transfer_characteristics"],
                            f"Unknown ({bitstream_details['transfer_characteristics']})",
                        )
                    )

                if isinstance(bitstream_details.get("matrix_coefficients"), int):
                    bitstream_details["matrix_coefficients"] = (
                        MATRIX_COEFFICIENTS_MAP.get(
                            bitstream_details["matrix_coefficients"],
                            f"Unknown ({bitstream_details['matrix_coefficients']})",
                        )
                    )

                if isinstance(bitstream_details.get("video_full_range_flag"), int):
                    bitstream_details["color_range"] = (
                        "full"
                        if bitstream_details["video_full_range_flag"] == 1
                        else "tv"
                    )

                if bitstream_details.get("matrix_coefficients") != "Unknown":
                    bitstream_details["color_space"] = bitstream_details[
                        "matrix_coefficients"
                    ]
                if bitstream_details.get("transfer_characteristics") != "Unknown":
                    bitstream_details["color_transfer"] = bitstream_details[
                        "transfer_characteristics"
                    ]

            elif nal_unit_type in (39, 40):
                logger.debug(f"Parsing SEI NAL unit (type {nal_unit_type}).")
                sei_pos = 0
                while sei_pos < len(nal_payload):
                    payload_type = 0
                    while sei_pos < len(nal_payload) and nal_payload[sei_pos] == 0xFF:
                        payload_type += 255
                        sei_pos += 1
                    if sei_pos >= len(nal_payload):
                        break
                    payload_type += nal_payload[sei_pos]
                    sei_pos += 1

                    payload_size = 0
                    while sei_pos < len(nal_payload) and nal_payload[sei_pos] == 0xFF:
                        payload_size += 255
                        sei_pos += 1
                    if sei_pos >= len(nal_payload):
                        break
                    payload_size += nal_payload[sei_pos]
                    sei_pos += 1

                    if sei_pos + payload_size > len(nal_payload):
                        logger.warning(
                            f"Invalid SEI payload size {payload_size} for type {payload_type} at sei_pos {sei_pos}. Skipping rest of NAL."
                        )
                        break

                    current_payload_data = nal_payload[sei_pos : sei_pos + payload_size]
                    logger.debug(
                        f"Processing SEI payload type {payload_type}, size {payload_size}"
                    )

                    try:
                        if payload_type == 137:
                            if len(current_payload_data) >= 24:
                                bitstream_details["transfer_characteristics"] = (
                                    "smpte2084"
                                )
                                if (
                                    bitstream_details["color_primaries"] == "Unknown"
                                    or bitstream_details["color_primaries"] == "bt709"
                                ):
                                    bitstream_details["color_primaries"] = "bt2020"
                                logger.debug(
                                    "Found Mastering Display Colour Volume (HDR10) SEI."
                                )
                        elif payload_type == 144:
                            if len(current_payload_data) >= 4:
                                max_cll, max_fall = struct.unpack(
                                    ">HH", current_payload_data[:4]
                                )
                                bitstream_details["max_content_light_level"] = max_cll
                                bitstream_details["max_frame_average_light_level"] = (
                                    max_fall
                                )
                                logger.debug(
                                    f"Found Content Light Level SEI: MaxCLL={max_cll}, MaxFALL={max_fall}"
                                )
                        elif payload_type == 5:
                            if (
                                len(current_payload_data) > 16
                                and current_payload_data[:12]
                                == b"\x44\x4f\x56\x49\x03\x01\x01\x08\x00\x00\x00\x00"
                            ):
                                logger.debug(
                                    f"Raw Dolby Vision data (payload_type 5): {current_payload_data.hex()}"
                                )
                                if len(current_payload_data) >= 27:
                                    val = current_payload_data[25]
                                    bitstream_details["dolby_vision_profile"] = (
                                        val >> 1
                                    ) & 0x7F
                                    bitstream_details["dolby_vision_level"] = (
                                        current_payload_data[26] & 0x3F
                                    )
                                    bitstream_details["hdr_format"] = "Dolby Vision"
                                    logger.debug(
                                        f"Found Dolby Vision SEI (heuristic): profile={bitstream_details['dolby_vision_profile']}, level={bitstream_details['dolby_vision_level']}"
                                    )
                        elif payload_type == 147:
                            if len(current_payload_data) >= 1:
                                transfer = current_payload_data[0]
                                if transfer == 18:
                                    bitstream_details["transfer_characteristics"] = (
                                        "arib-std-b67"
                                    )
                                    bitstream_details["hdr_format"] = "HLG"
                                    logger.debug(
                                        "Found Alternative Transfer Characteristics (HLG) SEI."
                                    )
                    except Exception as e:
                        logger.error(
                            f"Error parsing SEI payload type {payload_type}: {e}"
                        )

                    sei_pos += payload_size
            pos = nal_end

        if bitstream_details["dolby_vision_profile"] is not None:
            bitstream_details["hdr_format"] = "Dolby Vision"
            if bitstream_details["color_primaries"] == "Unknown":
                bitstream_details["color_primaries"] = "bt2020"
            if bitstream_details["transfer_characteristics"] == "Unknown":
                bitstream_details["transfer_characteristics"] = "smpte2084"
            if bitstream_details["matrix_coefficients"] == "Unknown":
                bitstream_details["matrix_coefficients"] = "bt2020nc"

        elif bitstream_details["transfer_characteristics"] == "arib-std-b67":
            bitstream_details["hdr_format"] = "HLG"
        elif bitstream_details["transfer_characteristics"] == "smpte2084":
            bitstream_details["hdr_format"] = "HDR (PQ)"

        logger.debug(f"Bitstream parsing result: {bitstream_details}")
        return bitstream_details
