# metaspector/cli.py
# !/usr/env/bin python3

"""
cli.py
~~~~~~~~~~~~~~~

This module provides the command-line interface for the metaspector library.
"""

import argparse
import json
import sys
import os
from urllib.parse import urlparse, unquote

from .inspector import MediaInspector
from ._exceptions import MetaspectorError


def check_source_path(path):
    """Custom type function for argparse to validate if a path is a file or a URL."""
    if path.startswith(("http://", "https://")):
        return path
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError(
            f"The path '{path}' does not exist or is not a file."
        )
    return path


def inspect(args):
    """Handles the 'inspect' subcommand."""
    try:
        inspector = MediaInspector(args.filepath)
        metadata = inspector.inspect(section=args.section)
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
    except (
            MetaspectorError,
            FileNotFoundError,
            ValueError,
            IOError,
    ) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


def export(args):
    """Handles the 'export' subcommand for both cover art and metadata."""
    try:
        inspector = MediaInspector(args.filepath)
        destination_path = args.destination

        if args.filepath.startswith(("http://", "https://")):
            parsed_url = urlparse(args.filepath)
            filename = os.path.basename(unquote(parsed_url.path))
            base_name = os.path.splitext(filename)[0]
        else:
            base_name = os.path.splitext(os.path.basename(args.filepath))[0]

        if not base_name:
            base_name = "media_export"

        # --- Logic for exporting the cover ---
        if args.export_type == "cover":
            cover_art = inspector.get_cover_art()
            if not cover_art:
                print("Error: No cover art found in the file.", file=sys.stderr)
                sys.exit(1)

            extension = ".jpg"
            if cover_art.startswith(b"\x89PNG"):
                extension = ".png"
            default_filename = f"{base_name}{extension}"

            if os.path.isdir(destination_path):
                output_path = os.path.join(destination_path, default_filename)
            else:
                output_path = destination_path

            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            with open(output_path, "wb") as f:
                f.write(cover_art)
            print(f"Cover art exported successfully to '{output_path}'.")

        # --- Logic for exporting metadata ---
        elif args.export_type == "meta":
            metadata = inspector.inspect()
            default_filename = f"{base_name}.json"

            if os.path.isdir(destination_path):
                output_path = os.path.join(destination_path, default_filename)
            else:
                output_path = destination_path

            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            json_data = json.dumps(metadata, indent=2, ensure_ascii=False)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_data)
            print(f"Metadata exported successfully to '{output_path}'.")

    except (MetaspectorError, FileNotFoundError, IOError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Defines the command-line entry point for the tool."""
    parser = argparse.ArgumentParser(
        description="Inspect and extract metadata from media files or URLs.",
        epilog="Use 'metaspector <command> --help' for more information on a specific command.",
    )

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    # --- Parser for the 'inspect' command ---
    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect a media file/URL and print its metadata as JSON.",
        epilog=(
            "Example: metaspector inspect /path/to/my_video.mp4\n"
            "Example: metaspector inspect https://example.com/audio.flac --section audio"
        ),
    )
    inspect_parser.add_argument(
        "filepath",
        type=check_source_path,
        help="The full path or URL to the media file to inspect.",
    )
    inspect_parser.add_argument(
        "--section",
        choices=["metadata", "audio", "video", "subtitle"],
        help="Optional: Specify a section to output (e.g., 'audio', 'metadata').",
    )
    inspect_parser.set_defaults(func=inspect)

    # --- Parser for the 'export' command ---
    export_parser = subparsers.add_parser(
        "export",
        help="Export data (cover art or metadata) from a media file/URL.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Export cover art from a URL to a specific file\n"
            "  metaspector export cover https://example.com/song.flac /covers/art.jpg\n\n"
            "  # Export metadata from a local file to a directory\n"
            "  metaspector export meta song.mp3 /json_files/"
        ),
    )
    export_parser.add_argument(
        "export_type",
        choices=["cover", "meta"],
        help="The type of data to export: 'cover' for the cover art or 'meta' for metadata JSON.",
    )
    export_parser.add_argument(
        "filepath",
        type=check_source_path,
        help="The full path or URL to the media file to export from.",
    )
    export_parser.add_argument(
        "destination",
        help="The destination path. Can be a full file path or a directory.",
    )
    export_parser.set_defaults(func=export)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)


if __name__ == "__main__":
    main()