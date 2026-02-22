"""Unit tests for FileService — uses tmp_path, no Qt required."""

import pytest

from src.models.text_document import TextDocument
from src.services.file_service import FileService


@pytest.fixture
def svc():
    return FileService()


class TestOpenFile:
    def test_reads_utf8_file(self, svc, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world", encoding="utf-8")
        doc = svc.open_file(str(f))
        assert doc.content == "hello world"
        assert doc.filepath == str(f)

    def test_detected_encoding_stored(self, svc, tmp_path):
        f = tmp_path / "test.txt"
        f.write_bytes("hello".encode("utf-8"))
        doc = svc.open_file(str(f))
        assert isinstance(doc.encoding, str)
        assert len(doc.encoding) > 0

    def test_modified_is_false_on_open(self, svc, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")
        doc = svc.open_file(str(f))
        assert doc.modified is False

    def test_raises_file_not_found(self, svc):
        with pytest.raises(FileNotFoundError):
            svc.open_file("/nonexistent/path/file.txt")

    def test_reads_multiline_content(self, svc, tmp_path):
        f = tmp_path / "multi.txt"
        f.write_text("line1\nline2\nline3", encoding="utf-8")
        doc = svc.open_file(str(f))
        assert doc.content == "line1\nline2\nline3"


class TestSaveFile:
    def test_writes_content_to_disk(self, svc, tmp_path):
        filepath = str(tmp_path / "out.txt")
        doc = TextDocument(filepath=filepath, content="saved content")
        svc.save_file(doc)
        assert (tmp_path / "out.txt").read_text(encoding="utf-8") == "saved content"

    def test_save_round_trip(self, svc, tmp_path):
        filepath = str(tmp_path / "round.txt")
        doc = TextDocument(filepath=filepath, content="round trip")
        svc.save_file(doc)
        loaded = svc.open_file(filepath)
        assert loaded.content == "round trip"

    def test_raises_value_error_for_empty_filepath(self, svc):
        doc = TextDocument(filepath="", content="data")
        with pytest.raises(ValueError):
            svc.save_file(doc)

    def test_overwrites_existing_file(self, svc, tmp_path):
        f = tmp_path / "existing.txt"
        f.write_text("old content", encoding="utf-8")
        doc = TextDocument(filepath=str(f), content="new content")
        svc.save_file(doc)
        assert f.read_text(encoding="utf-8") == "new content"


class TestDetectEncoding:
    """Tests for _detect_encoding — module-level function in file_service.py."""

    def test_utf16_le_detected_by_chardet(self):
        """UTF-16 with BOM gives chardet confidence=1.0, exercising the chardet branch.

        Using encode('utf-16') emits a BOM so chardet reliably returns 'UTF-16'.
        Raw UTF-16-LE without BOM requires long content for chardet to reach the
        0.7 confidence threshold, making it fragile for short test strings.
        """
        pytest.importorskip("chardet")  # skip gracefully if chardet not installed
        from src.services.file_service import _detect_encoding

        # encode('utf-16') prepends a BOM; chardet returns 'UTF-16' with confidence=1.0
        raw = "hello world".encode("utf-16")
        encoding = _detect_encoding(raw)
        # chardet returns 'UTF-16' (with BOM) or 'utf-16le'/'utf-16-le' (without BOM)
        assert encoding.lower() in ("utf-16", "utf-16le", "utf-16-le")

    def test_falls_back_to_utf8_for_undetectable_bytes(self):
        """Empty bytes: chardet returns None encoding → fallback to utf-8."""
        from src.services.file_service import _detect_encoding

        encoding = _detect_encoding(b"")
        assert encoding == "utf-8"


class TestDetectEncodingNormalization:
    def test_ascii_content_returns_utf8(self):
        """Pure-ASCII bytes must be labelled utf-8, not ascii.

        chardet correctly identifies ASCII bytes as 'ascii'. We normalize to
        'utf-8' because ASCII is a proper subset of UTF-8 and saving as utf-8
        is always safe for ASCII content.
        """
        from src.services.file_service import _detect_encoding
        raw = b"hello world"  # pure ASCII
        assert _detect_encoding(raw) == "utf-8"

    def test_non_ascii_utf8_content_returns_utf8(self):
        """Non-ASCII UTF-8 bytes (é, ñ) must return utf-8."""
        from src.services.file_service import _detect_encoding
        raw = "café résumé naïve".encode("utf-8")
        assert _detect_encoding(raw) == "utf-8"


class TestAtomicSaveCleanup:
    """Verify temp file is cleaned up when os.replace fails (lines 70-75)."""

    def test_temp_file_removed_on_replace_failure(self, svc, tmp_path, monkeypatch):
        removed: list[str] = []

        def _failing_replace(src: str, dst: str) -> None:
            raise OSError("simulated disk full")

        monkeypatch.setattr("src.services.file_service.os.replace", _failing_replace)
        monkeypatch.setattr("src.services.file_service.os.unlink", lambda p: removed.append(p))

        doc = TextDocument(filepath=str(tmp_path / "out.txt"), content="data")
        with pytest.raises(OSError, match="simulated disk full"):
            svc.save_file(doc)

        assert len(removed) == 1, "temp file should have been unlinked on failure"
