"""Unit tests for TextDocument model."""
import pytest
from src.models.text_document import TextDocument


class TestTextDocument:
    def test_initialization_with_required_fields(self):
        doc = TextDocument(filepath="/tmp/test.txt", content="hello")
        assert doc.filepath == "/tmp/test.txt"
        assert doc.content == "hello"

    def test_default_encoding_is_utf8(self):
        doc = TextDocument(filepath="/tmp/test.txt", content="")
        assert doc.encoding == "utf-8"

    def test_default_modified_is_false(self):
        doc = TextDocument(filepath="/tmp/test.txt", content="")
        assert doc.modified is False

    def test_validate_returns_true_for_nonempty_filepath(self):
        doc = TextDocument(filepath="/tmp/test.txt", content="")
        assert doc.validate() is True

    def test_validate_returns_false_for_empty_filepath(self):
        doc = TextDocument(filepath="", content="hello")
        assert doc.validate() is False

    def test_custom_encoding_stored(self):
        doc = TextDocument(filepath="/tmp/f.txt", content="x", encoding="latin-1")
        assert doc.encoding == "latin-1"

    def test_modified_flag_settable(self):
        doc = TextDocument(filepath="/tmp/f.txt", content="x", modified=True)
        assert doc.modified is True
