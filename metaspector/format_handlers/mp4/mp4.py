# metaspector/format_handlers/mp4/mp4.py
# !/usr/bin/env python3

import struct

from typing import BinaryIO, Dict, Any, Optional, List
from metaspector.format_handlers.base import BaseMediaParser
from .mp4_utils import _read_box_header, _read_uint32, _read_uint64
from .mp4_boxes import MP4BoxParser


class Mp4Parser(BaseMediaParser):
    """
    Parses MP4/M4V files to extract audio, video, and subtitle track metadata.
    """

    class _TrackCharacteristics(MP4BoxParser._TrackCharacteristics):
        """
        Inherits _TrackCharacteristics from MP4BoxParser.
        This local class is kept for type hinting convenience within Mp4Parser.
        """

        pass

    def __init__(self):
        self.audio_tracks: List[Dict[str, Any]] = []
        self.subtitle_tracks: List[Dict[str, Any]] = []
        self.video_tracks: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        self.moov_duration: Optional[int] = None
        self.moov_timescale: Optional[int] = None

    def parse(self, f: BinaryIO) -> Dict[str, Any]:
        """Parses the MP4 file from the given binary stream."""
        self.audio_tracks = []
        self.subtitle_tracks = []
        self.video_tracks = []
        self.metadata = {}
        self.moov_duration = None
        self.moov_timescale = None

        file_size = f.seek(0, 2)
        f.seek(0)

        current_pos = 0
        while current_pos < file_size:
            f.seek(current_pos)
            box_type, _, _, box_end = _read_box_header(f)
            if not box_type:
                break

            if box_type == b"moov":
                self._parse_moov(f, box_end)
                if (
                    self.moov_duration
                    and self.moov_timescale
                    and self.moov_timescale > 0
                ):
                    duration_in_seconds = self.moov_duration / self.moov_timescale
                    self.metadata["length"] = int(duration_in_seconds * 1000)
                    for track in self.audio_tracks:
                        track["duration_seconds"] = duration_in_seconds
                    for track in self.video_tracks:
                        track["duration_seconds"] = duration_in_seconds
                break
            elif box_type == b"meta":
                self.metadata.update(MP4BoxParser.parse_meta(f, box_end))

            current_pos = box_end

        if self.metadata.get("media_type") == 1 and "content_rating" in self.metadata:
            self.metadata.pop("content_rating")

        final_audio_tracks = []
        for track in self.audio_tracks:
            ordered_track = self._order_audio_track(track)
            final_audio_tracks.append(ordered_track)

        final_metadata = self._process_metadata_for_output(self.metadata)

        return {
            "metadata": final_metadata,
            "video": self.video_tracks,
            "audio": final_audio_tracks,
            "subtitle": self.subtitle_tracks,
        }

    def get_cover_art(self, f: BinaryIO) -> Optional[bytes]:
        """
        Extracts the raw cover art from the MP4 file by finding the 'covr' atom.
        """
        file_size = f.seek(0, 2)
        f.seek(0)

        def search_in_container(
            container_start: int, container_end: int
        ) -> Optional[bytes]:
            current_pos = container_start
            while current_pos < container_end:
                f.seek(current_pos)
                box_type, _, box_start, box_end = _read_box_header(f)
                if not box_type or box_end > container_end:
                    break
                if box_type in (
                    b"moov",
                    b"udta",
                    b"meta",
                    b"ilst",
                    b"\xa9nam",
                    b"name",
                    b"titl",
                ):
                    search_start = box_start + 8
                    if box_type == b"meta":
                        search_start += 4
                    result = search_in_container(search_start, box_end)
                    if result:
                        return result
                if box_type == b"covr":
                    data_pos = box_start + 8
                    while data_pos < box_end:
                        f.seek(data_pos)
                        data_box_type, _, data_box_start, data_box_end = (
                            _read_box_header(f)
                        )
                        if not data_box_type or data_box_end > box_end:
                            break
                        if data_box_type == b"data":
                            f.seek(data_box_start + 8)
                            f.read(8)
                            return f.read(data_box_end - f.tell())
                        data_pos = data_box_end
                current_pos = box_end
            return None

        return search_in_container(0, file_size)

    def _order_audio_track(self, track: Dict[str, Any]) -> Dict[str, Any]:
        """Reorders audio track fields to place duration_seconds after bitrate_kbps."""
        ordered_keys = [
            "track_id",
            "handler_name",
            "language",
            "internationalized_language",
            "codec",
            "channels",
            "sample_rate",
            "bits_per_sample",
            "bitrate_kbps",
            "duration_seconds",
            "total_samples",
            "main_program_content",
            "original_content",
            "dubbed_translation",
            "voice_over_translation",
            "language_translation",
            "describes_video_for_accessibility",
            "enhances_speech_intelligibility",
            "auxiliary_content",
            "dolby_atmos",
        ]

        ordered_dict = {}
        for key in ordered_keys:
            if key in track:
                ordered_dict[key] = track.pop(key)

        ordered_dict.update(track)
        return ordered_dict

    def _process_metadata_for_output(
        self, raw_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Reorders and processes metadata fields for consistent output.
        """
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
            "itunesadvisory",
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
            "sort_name",
            "sort_artist",
            "sort_album",
            "compilation",
            "gapless_playback",
            "content_id",
            "owner",
            "purchase_date",
            "itunes_account",
            "itunes_country",
            "artist_id",
            "playlist_id",
            "geID",
            "composer_id",
            "external_id",
            "length",
            "itun_compilation",
        ]

        temp_data = {}
        for key in list(raw_metadata.keys()):
            temp_data[key] = raw_metadata.pop(key)

        for key_in_order in output_order:
            if key_in_order in temp_data:
                processed_metadata[key_in_order] = temp_data.pop(key_in_order)

        processed_metadata.update(temp_data)

        if "track_total" in processed_metadata:
            processed_metadata["track_total"] = str(processed_metadata["track_total"])
        if "disc_total" in processed_metadata:
            processed_metadata["disc_total"] = str(processed_metadata["disc_total"])

        return processed_metadata

    def _parse_moov(self, f: BinaryIO, moov_end: int):
        """Orchestrates the parsing of all boxes within the 'moov' box."""
        current_pos = f.tell()
        while current_pos < moov_end:
            f.seek(current_pos)
            box_type, _, _, box_end = _read_box_header(f)
            if not box_type or box_end > moov_end:
                break
            if box_type == b"mvhd":
                mvhd_data = MP4BoxParser.parse_mvhd(f, box_end)
                self.moov_duration = mvhd_data.get("duration")
                self.moov_timescale = mvhd_data.get("timescale")
            elif box_type == b"trak":
                self._parse_trak(f, box_end)
            elif box_type == b"udta":
                udta_current_pos = f.tell()
                while udta_current_pos < box_end:
                    f.seek(udta_current_pos)
                    udta_child_type, _, _, udta_child_end = _read_box_header(f)
                    if not udta_child_type or udta_child_end > box_end:
                        break
                    if udta_child_type == b"meta":
                        self.metadata.update(MP4BoxParser.parse_meta(f, udta_child_end))
                        break
                    udta_current_pos = udta_child_end
            elif box_type == b"meta":
                self.metadata.update(MP4BoxParser.parse_meta(f, box_end))
            current_pos = box_end
        f.seek(moov_end)

    def _parse_trak(self, f: BinaryIO, trak_end: int):
        """Parses a 'trak' box and assembles track information."""
        track_id: Optional[int] = None
        i18n_lang: Optional[str] = None
        hdlr_details: Dict[str, Any] = {}
        mdhd_details: Dict[str, Any] = {}
        track_chars = self._TrackCharacteristics()
        audio_info: Dict[str, Any] = {}
        video_info: Dict[str, Any] = {}
        first_chunk_offset: Optional[int] = None
        first_sample_size: Optional[int] = None
        total_sample_size: int = 0
        descriptive_track_name: Optional[str] = None
        total_samples: Optional[int] = None

        current_pos = f.tell()
        while current_pos < trak_end:
            f.seek(current_pos)
            box_type, _, box_start, box_end = _read_box_header(f)
            if not box_type or box_end > trak_end:
                break

            if box_type == b"tkhd":
                track_id = MP4BoxParser.parse_tkhd(f, box_end)
            elif box_type == b"udta":
                udta_chars, udta_name = MP4BoxParser.parse_udta(f, box_end)
                track_chars = udta_chars
                if udta_name and descriptive_track_name is None:
                    descriptive_track_name = udta_name
                f.seek(box_end)
            elif box_type == b"mdia":
                mdia_pos = f.tell()
                while mdia_pos < box_end:
                    f.seek(mdia_pos)
                    mdia_type, _, _, mdia_end = _read_box_header(f)
                    if not mdia_type or mdia_end > box_end:
                        break

                    if mdia_type == b"mdhd":
                        mdhd_details = MP4BoxParser.parse_mdhd(f, mdia_end)
                    elif mdia_type == b"hdlr":
                        hdlr_details = MP4BoxParser.parse_hdlr(f, mdia_end)
                    elif mdia_type == b"elng":
                        i18n_lang = MP4BoxParser.parse_elng(f, mdia_end)
                    elif mdia_type == b"minf":
                        minf_pos = f.tell()
                        while minf_pos < mdia_end:
                            f.seek(minf_pos)
                            minf_type, _, _, minf_end = _read_box_header(f)
                            if not minf_type or minf_end > mdia_end:
                                break
                            if minf_type == b"stbl":
                                stbl_pos = f.tell()
                                while stbl_pos < minf_end:
                                    f.seek(stbl_pos)
                                    stbl_type, _, stbl_box_start, stbl_end = (
                                        _read_box_header(f)
                                    )
                                    if not stbl_type or stbl_end > minf_end:
                                        break

                                    if stbl_type == b"stsd":
                                        if hdlr_details.get("type") == b"soun":
                                            audio_stsd_info = (
                                                MP4BoxParser.parse_stsd_audio(
                                                    f, stbl_end
                                                )
                                            )
                                            audio_info.update(audio_stsd_info)
                                        elif hdlr_details.get("type") == b"vide":
                                            video_stsd_info = (
                                                MP4BoxParser.parse_stsd_video(
                                                    f, stbl_end
                                                )
                                            )
                                            video_info.update(video_stsd_info)
                                        elif (
                                            hdlr_details.get("type")
                                            in (b"sbtl", b"subt")
                                            and descriptive_track_name is None
                                        ):
                                            temp_file_pos = f.tell()
                                            f.seek(stbl_box_start)
                                            subtitle_stsd_name = (
                                                MP4BoxParser.parse_stsd_subtitle(
                                                    f, stbl_end
                                                )
                                            )
                                            if subtitle_stsd_name:
                                                descriptive_track_name = (
                                                    subtitle_stsd_name
                                                )
                                            f.seek(temp_file_pos)
                                    elif stbl_type == b"stsz":
                                        f.seek(stbl_box_start + 8 + 4)
                                        uniform_size = _read_uint32(f)
                                        sample_count = _read_uint32(f)
                                        if sample_count is not None:
                                            total_samples = sample_count
                                            if uniform_size != 0:
                                                if first_sample_size is None:
                                                    first_sample_size = uniform_size
                                                total_sample_size = (
                                                    uniform_size * sample_count
                                                )
                                            else:
                                                sizes_data = f.read(sample_count * 4)
                                                if len(sizes_data) == sample_count * 4:
                                                    sizes = struct.unpack(
                                                        f">{sample_count}I", sizes_data
                                                    )
                                                    total_sample_size = sum(sizes)
                                                    if (
                                                        first_sample_size is None
                                                        and sizes
                                                    ):
                                                        first_sample_size = sizes[0]
                                    elif (
                                        stbl_type == b"stco"
                                        and first_chunk_offset is None
                                    ):
                                        f.seek(stbl_box_start + 8 + 4)
                                        entry_count = _read_uint32(f)
                                        if entry_count is not None and entry_count > 0:
                                            first_chunk_offset = _read_uint32(f)
                                    elif (
                                        stbl_type == b"co64"
                                        and first_chunk_offset is None
                                    ):
                                        f.seek(stbl_box_start + 8 + 4)
                                        entry_count = _read_uint32(f)
                                        if entry_count is not None and entry_count > 0:
                                            first_chunk_offset = _read_uint64(f)
                                    f.seek(stbl_end)
                                    stbl_pos = stbl_end
                            f.seek(minf_end)
                            minf_pos = minf_end
                    elif mdia_type == b"meta":
                        meta_content_start_pos = f.tell()
                        f.read(4)
                        temp_meta_pos = meta_content_start_pos + 4
                        while temp_meta_pos < mdia_end:
                            f.seek(temp_meta_pos)
                            (
                                meta_sub_child_type,
                                _,
                                meta_sub_child_start,
                                meta_sub_child_end,
                            ) = _read_box_header(f)
                            if not meta_sub_child_type or meta_sub_child_end > mdia_end:
                                break
                            if meta_sub_child_type == b"ilst":
                                ilst_current_pos = meta_sub_child_start + 8
                                while ilst_current_pos < meta_sub_child_end:
                                    f.seek(ilst_current_pos)
                                    item_type, _, item_start, item_end = (
                                        _read_box_header(f)
                                    )
                                    if not item_type or item_end > meta_sub_child_end:
                                        break
                                    item_child_pos = item_start + 8
                                    while item_child_pos < item_end:
                                        f.seek(item_child_pos)
                                        data_type, _, _, data_end = _read_box_header(f)
                                        if data_type == b"data":
                                            f.read(8)
                                            potential_name = MP4BoxParser.parse_qtss(
                                                f, data_end
                                            )
                                            if (
                                                potential_name
                                                and item_type == b"\xa9nam"
                                            ):
                                                descriptive_track_name = potential_name
                                                break
                                        item_child_pos = data_end
                                    if descriptive_track_name:
                                        break
                                    ilst_current_pos = item_end
                            if descriptive_track_name:
                                break
                            temp_meta_pos = meta_sub_child_end
                    f.seek(mdia_end)
                    mdia_pos = mdia_end
            current_pos = box_end

        lang = mdhd_details.get("lang", "und")
        track_duration = mdhd_details.get("duration")
        track_timescale = mdhd_details.get("timescale")
        handler_type = hdlr_details.get("type")
        final_track_name = (
            descriptive_track_name
            if descriptive_track_name
            else hdlr_details.get("name")
        )

        if handler_type == b"soun":
            if track_duration and track_timescale and total_sample_size > 0:
                duration_in_seconds = track_duration / track_timescale
                if duration_in_seconds > 0:
                    bitrate_bps = (total_sample_size * 8) / duration_in_seconds
                    audio_info["bitrate_kbps"] = int(bitrate_bps / 1000)

            if total_samples is not None:
                audio_info["total_samples"] = total_samples

            if audio_info.get("codec") == "ec-3":
                has_atmos = False
                if (
                    first_chunk_offset is not None
                    and first_sample_size is not None
                    and first_sample_size > 0
                ):
                    original_file_pos = f.tell()
                    try:
                        f.seek(first_chunk_offset)
                        frame_data = f.read(first_sample_size)
                        if b"\x03\xbb\xbb\x81" in frame_data:
                            has_atmos = True
                    finally:
                        f.seek(original_file_pos)
                audio_info["dolby_atmos"] = has_atmos

            self.audio_tracks.append(
                {
                    "track_id": track_id or 0,
                    "handler_name": final_track_name,
                    "language": lang,
                    "internationalized_language": i18n_lang,
                    **audio_info,
                    "main_program_content": track_chars.main_program_content,
                    "original_content": track_chars.original_content,
                    "dubbed_translation": track_chars.dubbed_translation,
                    "voice_over_translation": track_chars.voice_over_translation,
                    "language_translation": track_chars.language_translation,
                    "describes_video_for_accessibility": track_chars.describes_video_for_accessibility,
                    "enhances_speech_intelligibility": track_chars.enhances_speech_intelligibility,
                    "auxiliary_content": track_chars.auxiliary_content,
                }
            )

        elif handler_type in (b"sbtl", b"subt"):
            self.subtitle_tracks.append(
                {
                    "track_id": track_id or 0,
                    "handler_name": final_track_name,
                    "language": lang,
                    "internationalized_language": i18n_lang,
                    "main_program_content": track_chars.main_program_content,
                    "original_content": track_chars.original_content,
                    "auxiliary_content": track_chars.auxiliary_content,
                    "forced_only": track_chars.forced_only,
                    "language_translation": track_chars.language_translation,
                    "easy_to_read": track_chars.easy_to_read,
                    "describes_music_and_sound": track_chars.describes_music_and_sound,
                    "transcribes_spoken_dialog": track_chars.transcribes_spoken_dialog,
                }
            )

        elif handler_type == b"vide":
            if track_duration and track_timescale and total_sample_size > 0:
                duration_in_seconds = track_duration / track_timescale
                if duration_in_seconds > 0:
                    bitrate_bps = (total_sample_size * 8) / duration_in_seconds
                    video_info["bitrate_kbps"] = int(bitrate_bps / 1000)

            if total_samples is not None:
                video_info["total_samples"] = total_samples

            self.video_tracks.append(
                {
                    "track_id": track_id or 0,
                    "handler_name": final_track_name,
                    "language": lang,
                    "internationalized_language": i18n_lang,
                    **video_info,
                    "main_program_content": track_chars.main_program_content,
                    "original_content": track_chars.original_content,
                    "auxiliary_content": track_chars.auxiliary_content,
                }
            )

        f.seek(trak_end)
