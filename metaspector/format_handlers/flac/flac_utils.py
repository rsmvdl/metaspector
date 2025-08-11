# metaspector/format_handlers/flac/flac_utils.py
# !/usr/bin/env python3

from typing import Dict, Any


def order_audio_track(track: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Reorders audio track fields for consistent output and adds index."""
    track["index"] = index
    track["handler_name"] = "Audio"  # Hardcoded for consistency
    track["language"] = "und"  # Hardcoded for consistency

    ordered_keys = [
        "index",
        "handler_name",
        "language",
        "codec",
        "codec_tag_string",
        "channels",
        "channel_layout",
        "sample_rate",
        "bits_per_sample",
        "bitrate",
        "duration_seconds",
        "total_samples",
    ]
    ordered_dict = {key: track.get(key) for key in ordered_keys if key in track}
    ordered_dict.update(track)
    return ordered_dict


def process_metadata_for_output(raw_meta: Dict[str, Any]) -> Dict[str, Any]:
    """Reorders all metadata fields for consistent output."""
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
        "duration_seconds",
        "bitrate",
        "bpm",
        "release_date",
        "publisher",
        "isrc",
        "barcode",
        "upc",
        "media_type",
        "replaygain_track_gain",
        "replaygain_track_peak",
        "replaygain_album_gain",
        "replaygain_album_peak",
        "lyrics",
        "composer",
        "copyright",
        "has_cover_art",
        "cover_art_mime",
        "cover_art_dimensions",
        "comment",
        "encoder",
    ]

    # Create a new dictionary to hold the final ordered metadata
    processed_meta = {}

    temp_meta = raw_meta.copy()

    for key in output_order:
        if key in temp_meta:
            processed_meta[key] = temp_meta.pop(key)

    processed_meta.update(temp_meta)

    return processed_meta