"""FileService — all file system I/O for TextTools.

No Qt imports. Wraps file operations in TextDocument objects.
Called only from MainViewModel — never directly from the View.

Atomic save: writes to a temp file in the same directory then calls os.replace()
to swap atomically. This prevents partial-write corruption if the process dies mid-save.

Encoding detection: uses chardet if available and confidence >= 0.7. Falls back
to utf-8 otherwise. Decode errors use 'replace' to avoid crashing on binary content.
"""

import logging
import os
import tempfile

from src.models.text_document import TextDocument

logger = logging.getLogger(__name__)

_ENCODING_FALLBACK = "utf-8"
_ENCODING_MIN_CONFIDENCE = 0.7


class FileService:
    """Read and write text files, wrapping results in TextDocument."""

    def open_file(self, filepath: str) -> TextDocument:
        """Read a file and return a TextDocument.

        Args:
            filepath: Path to the file to read.

        Returns:
            TextDocument with decoded content and detected encoding.

        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If the file cannot be read.
            OSError: For other I/O failures.
        """
        logger.info("Opening file: %s", filepath)
        with open(filepath, "rb") as f:
            raw = f.read()
        encoding = _detect_encoding(raw)
        content = raw.decode(encoding, errors="replace")
        return TextDocument(filepath=filepath, content=content, encoding=encoding)

    def save_file(self, document: TextDocument) -> None:
        """Write document content to disk atomically.

        Args:
            document: TextDocument with filepath and content to write.

        Raises:
            ValueError: If document.filepath is empty.
            PermissionError: If the destination is not writable.
            OSError: For other I/O failures.
        """
        if not document.validate():
            raise ValueError("Document filepath is empty")

        logger.info("Saving file: %s", document.filepath)
        dirpath = os.path.dirname(os.path.abspath(document.filepath)) or "."
        fd, tmp_path = tempfile.mkstemp(dir=dirpath)
        try:
            with os.fdopen(fd, "w", encoding=document.encoding) as f:
                f.write(document.content)
            os.replace(tmp_path, document.filepath)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise


def _detect_encoding(raw: bytes) -> str:
    """Return the most likely encoding for raw bytes.

    Module-level so it can be tested without instantiating FileService.
    Falls back to utf-8 if chardet is unavailable or confidence is too low.
    Normalizes 'ascii' to 'utf-8' because ASCII is a proper subset of UTF-8
    and saving as utf-8 is always safe for ASCII content.
    """
    try:
        import chardet  # optional dependency

        result = chardet.detect(raw)
        if result["encoding"] and result["confidence"] >= _ENCODING_MIN_CONFIDENCE:
            detected = result["encoding"].lower()
            # ASCII is a valid subset of UTF-8; normalize to avoid confusing the UI.
            return "utf-8" if detected == "ascii" else result["encoding"]
    except ImportError:
        logger.debug("chardet not installed; defaulting to utf-8")
    return _ENCODING_FALLBACK
