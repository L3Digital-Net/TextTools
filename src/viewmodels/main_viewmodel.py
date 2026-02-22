"""MainViewModel — presentation logic for the TextTools main window.

Mediates between MainWindow (View) and the service layer.
No direct widget manipulation — communicates exclusively via signals.

ServiceProtocols are defined here (per CLAUDE.md: protocol is local to consumer).
If signal or slot signatures change, update MainWindow._connect_signals() in lockstep.
"""

import logging
import os
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

    def merge_documents(self, docs: list[TextDocument], separator: str) -> str: ...


class MainViewModel(QObject):
    """Presentation logic for the main window.

    Signals:
        document_loaded: Emitted with decoded file content ready for the editor.
            Only load_file emits this — clears the modified flag in the View.
        content_updated: Emitted by apply_cleaning and replace_all.
            In-memory transformations only — the View must NOT clear the modified flag.
        encoding_detected: Emitted with encoding name on file open.
        file_saved: Emitted with filepath after a successful save.
        error_occurred: Emitted with error message on any failure.
        status_changed: Emitted with status bar text.
        merge_list_changed: Emitted with list of display names (filename only) when
            the merge queue changes. View re-populates mergeFileList on receipt.
    """

    document_loaded = Signal(str)
    content_updated = Signal(str)  # emitted by apply_cleaning and replace_all
    encoding_detected = Signal(str)
    file_saved = Signal(str)
    error_occurred = Signal(str)
    status_changed = Signal(str)
    merge_list_changed = Signal(list)  # list[str] of display names

    def __init__(
        self,
        file_service: FileServiceProtocol,
        text_service: TextServiceProtocol,
    ) -> None:
        super().__init__()
        self._file_service = file_service
        self._text_service = text_service
        self._current_document: TextDocument | None = None
        # Merge queue — ordered list of absolute paths; separator inserted between files.
        self._merge_filepaths: list[str] = []
        self._merge_separator: str = "\n"

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
        content = (
            current_text if current_text is not None else self._current_document.content
        )
        cleaned = self._text_service.apply_options(content, options)
        self._current_document = TextDocument(
            filepath=self._current_document.filepath,
            content=cleaned,
            encoding=self._current_document.encoding,
            modified=True,
        )
        self.content_updated.emit(cleaned)
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
        content = (
            current_text if current_text is not None else self._current_document.content
        )
        count = content.count(find_term)
        new_content = content.replace(find_term, replace_term)
        self._current_document = TextDocument(
            filepath=self._current_document.filepath,
            content=new_content,
            encoding=self._current_document.encoding,
            modified=True,
        )
        self.content_updated.emit(new_content)
        noun = "occurrence" if count == 1 else "occurrences"
        self.status_changed.emit(f"Replaced {count} {noun}")

    @Slot(str)
    def convert_to_utf8(self, current_text: str) -> None:
        """Re-save the current document in UTF-8 encoding.

        Args:
            current_text: Live editor text from the View. Used as the content
                to save (preserves unsaved edits).

        No-op when no document is loaded or the file is already UTF-8.
        Encoding comparison normalises dashes so 'utf-8' and 'utf8' both match.
        """
        if self._current_document is None:
            self.status_changed.emit("No document loaded")
            return
        # Normalise: strip dashes and lowercase so 'UTF-8', 'utf-8', 'utf8' all match.
        # UTF-8-SIG is the chardet name for UTF-8 with a BOM — treat it as already UTF-8
        # to avoid needlessly re-saving BOM files.
        current_encoding = self._current_document.encoding.lower().replace("-", "")
        if current_encoding in {"utf8", "utf8sig"}:
            self.status_changed.emit("File is already UTF-8")
            return
        doc = TextDocument(
            filepath=self._current_document.filepath,
            content=current_text,
            encoding="utf-8",
        )
        try:
            self._file_service.save_file(doc)
            self._current_document = doc
            self.encoding_detected.emit("utf-8")
            self.file_saved.emit(doc.filepath)
            self.status_changed.emit(f"Converted to UTF-8: {doc.filepath}")
        except (ValueError, PermissionError, OSError) as e:
            msg = f"Cannot convert file: {e}"
            logger.error(msg)
            self.error_occurred.emit(msg)
            self.status_changed.emit("Error converting file")

    # ── Merge queue ────────────────────────────────────────────────────────────

    def _emit_merge_list(self) -> None:
        """Emit merge_list_changed with current display names (filename only)."""
        names = [os.path.basename(p) for p in self._merge_filepaths]
        self.merge_list_changed.emit(names)

    @Slot()
    def add_current_to_merge(self) -> None:
        """Append the currently loaded file's path to the merge queue."""
        if self._current_document is None:
            self.error_occurred.emit("No file loaded — open a file first")
            return
        path = self._current_document.filepath
        if path not in self._merge_filepaths:
            self._merge_filepaths.append(path)
            self._emit_merge_list()

    @Slot(list)
    def add_files_to_merge(self, filepaths: list[str]) -> None:
        """Append multiple filepaths to the merge queue; silently drop duplicates."""
        changed = False
        for path in filepaths:
            if path not in self._merge_filepaths:
                self._merge_filepaths.append(path)
                changed = True
        if changed:
            self._emit_merge_list()

    @Slot(int)
    def remove_from_merge(self, index: int) -> None:
        """Remove the item at the given index from the merge queue."""
        if 0 <= index < len(self._merge_filepaths):
            self._merge_filepaths.pop(index)
            self._emit_merge_list()

    @Slot(int, int)
    def move_merge_item(self, from_idx: int, to_idx: int) -> None:
        """Move merge queue item from from_idx to to_idx (before that position)."""
        n = len(self._merge_filepaths)
        if from_idx == to_idx or not (0 <= from_idx < n) or not (0 <= to_idx <= n):
            return
        item = self._merge_filepaths.pop(from_idx)
        # Adjust destination index after the pop when moving forward.
        insert_at = to_idx if to_idx <= from_idx else to_idx - 1
        self._merge_filepaths.insert(insert_at, item)
        self._emit_merge_list()

    @Slot(str)
    def set_merge_separator(self, sep: str) -> None:
        """Update the separator inserted between merged files."""
        self._merge_separator = sep

    @Slot()
    def execute_merge(self) -> None:
        """Read all queued files, merge with separator, emit document_loaded."""
        if not self._merge_filepaths:
            self.error_occurred.emit("No files in merge list")
            return
        docs: list[TextDocument] = []
        for path in self._merge_filepaths:
            try:
                docs.append(self._file_service.open_file(path))
            except (FileNotFoundError, PermissionError, OSError) as e:
                name = os.path.basename(path)
                self.error_occurred.emit(f"Cannot read {name}: {e}")
                return
        merged = self._text_service.merge_documents(docs, self._merge_separator)
        self.document_loaded.emit(merged)
        n = len(docs)
        noun = "file" if n == 1 else "files"
        self.status_changed.emit(f"Merged {n} {noun}")
