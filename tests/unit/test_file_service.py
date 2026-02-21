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
