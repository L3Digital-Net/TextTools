"""MainViewModel — presentation logic for the TextTools main window.

Mediates between MainWindow (View) and the service layer.
No direct widget manipulation — communicates exclusively via signals.

ServiceProtocols are defined here (per CLAUDE.md: protocol is local to consumer).
If signal or slot signatures change, update MainWindow._connect_signals() in lockstep.
"""

import logging
from typing import Protocol

from PySide6.QtCore import QObject, Signal, Slot

from src.models.cleaning_options import CleaningOptions
from src.models.text_document import TextDocument

logger = logging.getLogger(__name__)


class FileServiceProtocol(Protocol):
    """Interface required of any file service injected into MainViewModel."""

    def open_file(self, filepath: str) -> TextDocument: ...

    def save_file(self, document: TextDocument) -> None: ...


class TextServiceProtocol(Protocol):
    """Interface required of any text processing service injected into MainViewModel."""

    def apply_options(self, text: str, options: CleaningOptions) -> str: ...


class MainViewModel(QObject):
    """Presentation logic for the main window.

    Signals:
        document_loaded: Emitted with decoded file content ready for the editor.
        encoding_detected: Emitted with encoding name on file open.
        file_saved: Emitted with filepath after a successful save.
        error_occurred: Emitted with error message on any failure.
        status_changed: Emitted with status bar text.
    """

    document_loaded = Signal(str)
    encoding_detected = Signal(str)
    file_saved = Signal(str)
    error_occurred = Signal(str)
    status_changed = Signal(str)

    def __init__(
        self,
        file_service: FileServiceProtocol,
        text_service: TextServiceProtocol,
    ) -> None:
        super().__init__()
        self._file_service = file_service
        self._text_service = text_service
        self._current_document: TextDocument | None = None

    @Slot(str)
    def load_file(self, filepath: str) -> None:
        """Load a file from disk and emit its content for the editor."""
        logger.info("Loading file: %s", filepath)
        self.status_changed.emit(f"Loading {filepath}...")
        try:
            doc = self._file_service.open_file(filepath)
            self._current_document = doc
            self.document_loaded.emit(doc.content)
            self.encoding_detected.emit(doc.encoding)
            self.status_changed.emit(f"Opened: {filepath}")
        except (FileNotFoundError, PermissionError, OSError) as e:
            msg = f"Cannot open file: {e}"
            logger.error(msg)
            self.error_occurred.emit(msg)
            self.status_changed.emit("Error opening file")

    @Slot(str, str)
    def save_file(self, filepath: str, content: str) -> None:
        """Save editor content to a filepath."""
        logger.info("Saving to: %s", filepath)
        encoding = (
            self._current_document.encoding if self._current_document else "utf-8"
        )
        doc = TextDocument(filepath=filepath, content=content, encoding=encoding)
        try:
            self._file_service.save_file(doc)
            self._current_document = doc
            self.file_saved.emit(filepath)
            self.status_changed.emit(f"Saved: {filepath}")
        except (ValueError, PermissionError, OSError) as e:
            msg = f"Cannot save file: {e}"
            logger.error(msg)
            self.error_occurred.emit(msg)
            self.status_changed.emit("Error saving file")

    def apply_cleaning(
        self, options: CleaningOptions, current_text: str | None = None
    ) -> None:
        """Apply text cleaning to the given text or current document content.

        Args:
            options: Cleaning flags to apply.
            current_text: Live editor text from the View. When provided, takes
                precedence over _current_document.content so user edits typed
                after file-load are not discarded. When None, falls back to the
                last-loaded document content (backward-compatible default).

        No-op when no document is loaded.
        """
        if self._current_document is None:
            self.status_changed.emit("No document loaded")
            return
        # Prefer live editor text over stale document state — avoids overwriting
        # user edits when a cleaning checkbox is toggled after in-editor typing.
        content = current_text if current_text is not None else self._current_document.content
        cleaned = self._text_service.apply_options(content, options)
        self._current_document = TextDocument(
            filepath=self._current_document.filepath,
            content=cleaned,
            encoding=self._current_document.encoding,
            modified=True,
        )
        self.document_loaded.emit(cleaned)
        self.status_changed.emit("Text cleaned")

    def replace_all(
        self, find_term: str, replace_term: str, current_text: str | None = None
    ) -> None:
        """Replace all occurrences of find_term in the given text or current document.

        Args:
            find_term: String to search for.
            replace_term: String to substitute.
            current_text: Live editor text from the View. When provided, takes
                precedence over _current_document.content so user edits typed
                after file-load are not discarded. When None, falls back to the
                last-loaded document content (backward-compatible default).

        No-op when no document is loaded or find_term is empty.
        """
        if self._current_document is None or not find_term:
            return
        # Prefer live editor text over stale document state — mirrors apply_cleaning.
        content = current_text if current_text is not None else self._current_document.content
        count = content.count(find_term)
        new_content = content.replace(find_term, replace_term)
        self._current_document = TextDocument(
            filepath=self._current_document.filepath,
            content=new_content,
            encoding=self._current_document.encoding,
            modified=True,
        )
        self.document_loaded.emit(new_content)
        noun = "occurrence" if count == 1 else "occurrences"
        self.status_changed.emit(f"Replaced {count} {noun}")

