"""TextDocument — core domain model for a loaded text file.

This is the primary data transfer object between FileService and MainViewModel.
If fields change, update FileService.open_file() and MainViewModel._current_document
references accordingly.
"""

from dataclasses import dataclass


@dataclass
class TextDocument:
    """A text file loaded into memory with its metadata.

    Attributes:
        filepath: Absolute or relative path to the source file.
        content: Decoded text content of the file.
        encoding: Character encoding used to decode the file.
        modified: True if content has been changed since last save.
    """

    filepath: str
    content: str
    encoding: str = "utf-8"
    modified: bool = False

    def validate(self) -> bool:
        """Return True if this document has a non-empty filepath."""
        return len(self.filepath) > 0
