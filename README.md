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

```bash
pip install metaspector
```

---

## 💡 Usage

### Command-Line Interface (CLI)

The metaspector CLI provides simple and direct access to the library's main functions.

#### Inspect a File

To inspect a file and print all of its metadata to the terminal as JSON, use the `inspect` command:

```bash
metaspector inspect "/path/to/your/file.mp4"
```

#### Inspect a Specific Section

You can specify a section to get a more focused output. For example, to view only the audio track details:

```bash
metaspector inspect "/path/to/your/file.m4a" --section audio
```

#### Export Metadata

To export the full metadata of a file to a JSON file, use the `export` command with the `meta` type:

```bash
metaspector export meta "/path/to/your/file.mp3" "./output/"
```

This command will create a file named `your_file.json` in the `./output/` directory.

#### Export Cover Art

To extract and save the embedded cover art, use the `export` command with the `cover` type:

```bash
metaspector export cover "/path/to/your/file.flac" "./output/"
```

This will save the image as `your_file.jpg` or `your_file.png` in the `./output/` directory.

---

### Python API

Metaspector's API is designed for easy integration into your Python scripts.

#### Basic Inspection

To get all metadata from a file, instantiate `MediaInspector` and call the `inspect()` method:

```python
from metaspector import MediaInspector

inspector = MediaInspector("/path/to/your/file.mp4")
metadata = inspector.inspect()

print(metadata)
```

#### Get Specific Sections

You can pass the `section` argument to the `inspect()` method to retrieve only a specific part of the metadata:

```python
from metaspector import MediaInspector

inspector = MediaInspector("/path/to/your/file.m4a")
audio_data = inspector.inspect(section="audio")

print(audio_data)
```

#### Extract Cover Art

Use the `get_cover_art()` method to retrieve the raw image bytes, which you can then save to a file:

```python
from metaspector import MediaInspector

inspector = MediaInspector("/path/to/your/file.flac")
cover_art_bytes = inspector.get_cover_art()

if cover_art_bytes:
    with open("cover.jpg", "wb") as f:
        f.write(cover_art_bytes)
```
