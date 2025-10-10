# metaspector/format_handlers/base.py
# !/usr/bin/env python3

from abc import ABC, abstractmethod
from typing import BinaryIO, Dict, List, Any


class BaseMediaParser(ABC):
    """
    Abstract base class for media file format parsers.
    Defines the interface that all concrete media parsers must implement.
    """

    @abstractmethod
    def parse(self, f: BinaryIO) -> Dict[str, List]:
        """
        Parses the media file from the given binary stream and
        returns a dictionary of extracted track metadata.

        Args:
            f: A binary file-like object (e.g., an open file handle)
               positioned at the beginning of the relevant data.

        Returns:
            A dictionary with 'audio' and 'subtitle' keys, each containing
            a list of dictionaries, where each inner dictionary represents
            metadata for a track.
            Example: {"audio": [...], "subtitle": [...]}
        """
        pass
