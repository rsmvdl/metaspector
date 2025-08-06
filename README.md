# Metaspector

**Metaspector** is a powerful Python library and command-line tool designed for **inspecting and extracting metadata** from various media file formats. Whether you need to programmatically access track information, album art, or simply get a quick overview of a file's properties, Metaspector provides a clean and consistent interface.

---

## ✨ Features

* **Comprehensive Metadata Extraction**: Retrieve detailed information like title, artist, album, genre, release date, track numbers, and more.

* **Audio and Video Track Details**: Get specifics about video/audio codecs, channels, sample rates, bitrates, video dimensions, and more.

* **Subtitle Track Details**: Get a wide variety of subtitle specific metadata like "forced only", "auxiliary content", "language translation" etc.

* **Cover Art Extraction**: Easily extract embedded cover art.

* **Multi-Format Support**: Currently supports:

    * 🎬 **MP4/M4V/M4A** (MPEG-4 incl. parsing of proprietary atoms often seen in M4V files distributed by Apple Inc.)

    * 🎵 **MP3** (MPEG-1 Audio Layer III)

    * 🎧 **FLAC** (Free Lossless Audio Codec)

* **Flexible Output**:

    * **CLI**: Get human-readable JSON output directly in your terminal.

    * **API**: Integrate seamlessly into your Python applications.

* **Section-Specific Output**: Request only the `metadata`, `audio`, `video`, or `subtitle` sections for focused data retrieval.

* **Export Functionality**: Export extracted metadata to JSON files or cover art to image files.

* **No Dependencies**: Metaspector is a lightweight, self-contained library. It relies exclusively on built-in Python tools, requiring no external libraries to run. 
---

## 🚀 Installation

You can install `metaspector` directly from PyPI using pip:

```markdown
pip install metaspector
