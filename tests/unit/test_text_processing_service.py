"""Unit tests for TextProcessingService — no Qt required."""

import pytest

from src.models.cleaning_options import CleaningOptions
from src.services.text_processing_service import TextProcessingService


@pytest.fixture
def svc():
    return TextProcessingService()


class TestTrimWhitespace:
    def test_strips_leading_blank_lines(self, svc):
        result = svc.trim_whitespace("\n\nhello")
        assert result == "hello"

    def test_strips_trailing_blank_lines(self, svc):
        result = svc.trim_whitespace("hello\n\n")
        assert result == "hello"

    def test_strips_trailing_spaces_from_each_line(self, svc):
        result = svc.trim_whitespace("hello   \nworld   ")
        assert result == "hello\nworld"

    def test_preserves_internal_blank_lines(self, svc):
        result = svc.trim_whitespace("para1\n\npara2")
        assert result == "para1\n\npara2"

    def test_empty_string_returns_empty(self, svc):
        assert svc.trim_whitespace("") == ""

    def test_only_whitespace_returns_empty(self, svc):
        assert svc.trim_whitespace("   \n  \n") == ""


class TestCleanWhitespace:
    def test_collapses_multiple_spaces(self, svc):
        result = svc.clean_whitespace("hello    world")
        assert result == "hello world"

    def test_single_space_unchanged(self, svc):
        result = svc.clean_whitespace("hello world")
        assert result == "hello world"

    def test_preserves_line_breaks(self, svc):
        result = svc.clean_whitespace("line1\nline2")
        assert result == "line1\nline2"

    def test_collapses_per_line(self, svc):
        result = svc.clean_whitespace("a  b\nc   d")
        assert result == "a b\nc d"

    def test_empty_string(self, svc):
        assert svc.clean_whitespace("") == ""


class TestRemoveTabs:
    def test_removes_leading_tab(self, svc):
        result = svc.remove_tabs("\thello")
        assert result == "hello"

    def test_removes_leading_spaces(self, svc):
        result = svc.remove_tabs("   hello")
        assert result == "hello"

    def test_removes_mixed_leading_whitespace(self, svc):
        result = svc.remove_tabs("\t  hello")
        assert result == "hello"

    def test_preserves_non_leading_whitespace(self, svc):
        result = svc.remove_tabs("hello\tworld")
        assert result == "hello\tworld"

    def test_processes_each_line(self, svc):
        result = svc.remove_tabs("\tline1\n\tline2")
        assert result == "line1\nline2"

    def test_empty_string(self, svc):
        assert svc.remove_tabs("") == ""


class TestApplyOptions:
    def test_no_options_returns_unchanged(self, svc):
        text = "  hello  \n  world  "
        result = svc.apply_options(text, CleaningOptions())
        assert result == text

    def test_trim_only(self, svc):
        result = svc.apply_options("\nhello\n", CleaningOptions(trim_whitespace=True))
        assert result == "hello"

    def test_clean_only(self, svc):
        result = svc.apply_options("a  b", CleaningOptions(clean_whitespace=True))
        assert result == "a b"

    def test_remove_tabs_only(self, svc):
        result = svc.apply_options("\thello", CleaningOptions(remove_tabs=True))
        assert result == "hello"

    def test_all_options_compose(self, svc):
        text = "\n\t  hello    world  \n\n"
        opts = CleaningOptions(
            trim_whitespace=True, clean_whitespace=True, remove_tabs=True
        )
        result = svc.apply_options(text, opts)
        assert result == "hello world"
